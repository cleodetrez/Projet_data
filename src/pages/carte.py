"""carte choroplèthe par département (version flask)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json

from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px

# import local avec repli pour éviter E0401 lors de l'analyse statique
try:
    from src.utils.get_data import query_db  # type: ignore
except ImportError:  # pragma: no cover
    def query_db(*args, **kwargs):  # noqa: D401
        """stub pour pylint en absence du module au linting."""
        raise ImportError("src.utils.get_data introuvable")

# déclaration du blueprint flask
carte_bp = Blueprint("carte", __name__, url_prefix="/carte")

# chemin absolu vers le geojson
ROOT = Path(__file__).resolve().parents[2]
GEOJSON_DEPTS_PATH = ROOT / "departements-version-simplifiee.geojson"


# --- fonctions utilitaires ---
@lru_cache(maxsize=1)
def _load_departements_geojson() -> dict:
    """charge une seule fois le geojson des départements."""
    with GEOJSON_DEPTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _detect_featureidkey(geojson: dict) -> str:
    """détecte automatiquement la clé featureidkey probable dans le geojson."""
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
    """assure la présence des colonnes nécessaires et normalise le code département."""
    df = df.copy()
    if "dep" in df.columns and "dept" not in df.columns:
        df = df.rename(columns={"dep": "dept"})

    required = {"dept", "accidents"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"colonnes manquantes dans df: {missing}")

    # normalisation du code département, en conservant les non numériques (ex: 2A, 2B)
    def _norm_dept(v: str) -> str:
        v = str(v).strip()
        if v.isdigit() and len(v) < 2:
            return v.zfill(2)
        return v

    df["dept"] = df["dept"].astype(str).str.strip().apply(_norm_dept)

    if "population" in df.columns:
        def _taux(row) -> float | None:
            pop = row.get("population", 0)
            return (row["accidents"] / pop * 100_000.0) if pop else None

        df["taux_100k"] = df.apply(_taux, axis=1)

    return df


def _build_figure(df: pd.DataFrame, metric: str):
    """construit la carte choroplèthe plotly."""
    geojson = _load_departements_geojson()
    featureidkey = _detect_featureidkey(geojson)
    if metric not in df.columns:
        raise ValueError(f"colonne '{metric}' absente du dataframe.")

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="dept",
        color=metric,
        featureidkey=featureidkey,
        projection="mercator",
        color_continuous_scale="Blues",
        hover_name="dept",
        labels={
            "accidents": "Accidents",
            "taux_100k": "Taux pour 100 000 hab.",
        },
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        coloraxis_colorbar={"title": "Valeur"},
        template="plotly_white",
        title={"text": "Accidentologie par département (France)", "x": 0.5},
    )

    return fig


# --- route flask principale ---
@carte_bp.route("/", methods=["GET"])
def show_carte():
    """affiche la page avec la carte choroplèthe."""
    # paramètres GET (ex: /carte?annee=2023&metrique=accidents)
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
    except (ValueError, ConnectionError, TimeoutError) as err:
        return render_template(
            "carte.html",
            plot_html=None,
            error=f"erreur sql : {err}",
        )

    if df is None or df.empty:
        return render_template(
            "carte.html",
            plot_html=None,
            error="aucune donnée disponible",
        )

    try:
        df = _ensure_dataframe_schema(df)
    except (ValueError, KeyError, TypeError) as err:
        return render_template(
            "carte.html",
            plot_html=None,
            error=f"données invalides : {err}",
        )

    if metric == "taux_100k" and "taux_100k" not in df.columns:
        metric = "accidents"

    fig = _build_figure(df, metric)
    plot_html = fig.to_html(full_html=False)

    return render_template(
        "carte.html",
        plot_html=plot_html,
        error=None,
        year=year,
        metric=metric,
    )
