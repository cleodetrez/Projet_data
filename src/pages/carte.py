"""
Carte choroplèthe par département (version Flask)
"""
from __future__ import annotations
from flask import Blueprint, render_template, request
from functools import lru_cache
from pathlib import Path
from typing import Optional
import json
import pandas as pd
import plotly.express as px
from src.utils.get_data import query_db

# Déclaration du Blueprint Flask
carte_bp = Blueprint("carte", __name__, url_prefix="/carte")

# Chemin absolu vers le GeoJSON
ROOT = Path(__file__).resolve().parents[2]
GEOJSON_DEPTS_PATH = ROOT / "departements-version-simplifiee.geojson"


# --- Fonctions utilitaires (inchangées ou légèrement adaptées) ---
@lru_cache(maxsize=1)
def _load_departements_geojson() -> dict:
    """Charge une seule fois le GeoJSON des départements."""
    with GEOJSON_DEPTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _detect_featureidkey(geojson: dict) -> str:
    """Détecte automatiquement la clé featureidkey la plus probable dans le GeoJSON."""
    features = geojson.get("features", [])
    if not features:
        return "properties.code"
    props = features[0].get("properties", {})
    candidates = list(props.keys())
    for k in ("code", "insee", "dep", "CODE_DEPT", "code_dept", "dept"):
        for pk in candidates:
            if k.lower() in pk.lower():
                return f"properties.{pk}"
    return f"properties.{candidates[0]}" if candidates else "properties.code"


def _ensure_dataframe_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Assure la présence des colonnes nécessaires et normalise le code département."""
    df = df.copy()
    if "dep" in df.columns and "dept" not in df.columns:
        df = df.rename(columns={"dep": "dept"})

    required = {"dept", "accidents"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans df: {missing}")

    df["dept"] = df["dept"].astype(str).str.strip().apply(lambda v: v.zfill(2) if v.isdigit() and len(v) < 2 else v)

    if "population" in df.columns:
        df["taux_100k"] = df.apply(
            lambda r: (r["accidents"] / r["population"] * 100000.0) if r.get("population", 0) else None,
            axis=1,
        )

    return df


def _build_figure(df: pd.DataFrame, metric: str):
    """Construit la carte choroplèthe Plotly."""
    geojson = _load_departements_geojson()
    featureidkey = _detect_featureidkey(geojson)
    if metric not in df.columns:
        raise ValueError(f"Colonne '{metric}' absente du dataframe.")

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="dept",
        color=metric,
        featureidkey=featureidkey,
        projection="mercator",
        color_continuous_scale="Blues",
        hover_name="dept",
        labels={"accidents": "Accidents", "taux_100k": "Taux pour 100 000 hab."},
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(title="Valeur"),
        template="plotly_white",
        title=dict(text="Accidentologie par département (France)", x=0.5),
    )

    return fig


# --- Route Flask principale ---
@carte_bp.route("/", methods=["GET"])
def show_carte():
    """Affiche la page avec la carte choroplèthe."""
    # Récupération des paramètres GET (ex: /carte?annee=2023&metrique=accidents)
    year = request.args.get("annee", default=2023, type=int)
    metric = request.args.get("metrique", default="accidents", type=str)

    try:
        sql = """
        SELECT dep AS dept, COUNT(*) AS accidents
        FROM caracteristiques
        WHERE annee = :year OR (annee IS NULL AND :year IS NULL)
        GROUP BY dep
        """
        df = query_db(sql, {"year": year})
    except Exception as e:
        return render_template("carte.html", plot_html=None, error=f"Erreur SQL : {e}")

    if df is None or df.empty:
        return render_template("carte.html", plot_html=None, error="Aucune donnée disponible")

    try:
        df = _ensure_dataframe_schema(df)
    except Exception as e:
        return render_template("carte.html", plot_html=None, error=f"Données invalides : {e}")

    if metric == "taux_100k" and "taux_100k" not in df.columns:
        metric = "accidents"

    fig = _build_figure(df, metric)
    plot_html = fig.to_html(full_html=False)

    return render_template("carte.html", plot_html=plot_html, error=None, year=year, metric=metric)