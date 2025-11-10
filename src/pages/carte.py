"""
carte clorophete par dep
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from functools import lru_cache
from pathlib import Path
from typing import Optional

import json
import pandas as pd
import plotly.express as px
from dash import html, dcc, Input, Output, callback

from src.utils.get_data import query_db

GEOJSON_DEPTS_PATH = Path("data/communes.geojson")

#from src.utils.db_queries import get_accidents_by_departement


@lru_cache(maxsize=1)
def _load_departements_geojson() -> dict:
    """Charge une seule fois le GeoJSON des départements."""
    with GEOJSON_DEPTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _detect_featureidkey(geojson: dict) -> str:
    """Détecte automatiquement la clé featureidkey la plus probable dans le GeoJSON."""
    # cherche parmi les propriétés du premier feature
    features = geojson.get("features", [])
    if not features:
        return "properties.code"
    props = features[0].get("properties", {})
    candidates = list(props.keys())
    # priorités simples
    for k in ("code", "insee", "dep", "CODE_DEPT", "code_dept", "dept"):
        for pk in candidates:
            if k.lower() in pk.lower():
                return f"properties.{pk}"
    # fallback au premier champ probable
    if candidates:
        return f"properties.{candidates[0]}"
    return "properties.code"

def _ensure_dataframe_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assure la présence des colonnes nécessaires et normalise le code département.
    Exige au minimum : 'dept' et 'accidents'
    """
    df = df.copy()
    # accepter 'dep' ou 'dept'
    if "dep" in df.columns and "dept" not in df.columns:
        df = df.rename(columns={"dep": "dept"})
    required = {"dept", "accidents"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans df: {missing}")

    # dept en string, padding à 2 caractères si numérique
    df["dept"] = df["dept"].astype(str).str.strip()
    def pad_dep(v):
        if v.isdigit() and len(v) < 2:
            return v.zfill(2)
        return v
    df["dept"] = df["dept"].apply(pad_dep)

    if "population" in df.columns:
        df["taux_100k"] = df.apply(
            lambda r: (r["accidents"] / r["population"] * 100000.0) if r.get("population", 0) else None,
            axis=1,
        )

    return df


def _build_figure(df: pd.DataFrame, metric: str) -> "plotly.graph_objects.Figure":
    """
    Construit la carte choroplèthe.
    metric ∈ {'accidents', 'taux_100k'}
    """
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
        labels={
            "accidents": "Accidents",
            "taux_100k": "Taux pour 100 000 hab.",
        },
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(title="Valeur"),
        template="plotly_white",
        title=dict(text="Accidentologie par département (France)", x=0.5),
    )

    return fig


def layout():
    """Layout de la page choroplèthe (contrôles + graphique)"""
    return html.Div(
        [
            html.H2("Carte choroplèthe — accidents par département"),
            html.Div(
                [
                    # plsrs annees ?
                    html.Label("Année"),
                    dcc.Dropdown(
                        id="map-year",
                        options=[{"label": "2023", "value": 2023}],
                        value=2023,
                        clearable=False,
                        style={"width": "200px"},
                    ),
                    html.Label("Métrique"),
                    dcc.RadioItems(
                        id="map-metric",
                        options=[
                            {"label": "Nombre d'accidents", "value": "accidents"},
                            {"label": "Taux pour 100 000 hab.", "value": "taux_100k"},
                        ],
                        value="accidents",
                        inline=True,
                    ),
                ],
                style={"display": "flex", "gap": "24px", "alignItems": "center", "marginBottom": "12px"},
            ),
            dcc.Graph(id="map-choropleth", figure=px.scatter()),  # placeholder
        ],
        style={"maxWidth": "1100px", "margin": "0 auto", "padding": "12px"},
    )


@callback(
    Output("map-choropleth", "figure"),
    Input("map-year", "value"),
    Input("map-metric", "value"),
)

def update_map(year: Optional[int], metric: str):
    """
    Callback Dash : récupère les données (dep / accidents) depuis la base et reconstruit la carte.
    """
    # requête simple : nombre d'accidents par département pour l'année demandée
    # adapter le nom de la table/colonne si nécessaire (ici : caracteristiques avec colonne 'dep' ou 'dept')
    try:
        sql = """
        SELECT dep AS dept, COUNT(*) AS accidents
        FROM caracteristiques
        WHERE annee = :year OR (annee IS NULL AND :year IS NULL)
        GROUP BY dep
        """
        df = query_db(sql, {"year": year})
    except Exception as e:
        # si la requête échoue, renvoyer une figure d'erreur non bloquante
        return px.scatter(title=f"Aucune donnée: {e}")

    if df is None or df.empty:
        return px.scatter(title="Aucune donnée disponible")

    try:
        df = _ensure_dataframe_schema(df)
    except Exception as e:
        return px.scatter(title=f"Données invalides: {e}")

    if metric == "taux_100k" and "taux_100k" not in df.columns:
        metric = "accidents"

    return _build_figure(df, metric)
