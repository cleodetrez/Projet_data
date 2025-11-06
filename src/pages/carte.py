"""
carte clorophete par dep
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import json
import pandas as pd
import plotly.express as px
from dash import html, dcc, Input, Output, callback

GEOJSON_DEPTS_PATH = Path("data/communes.geojson")

#from src.utils.db_queries import get_accidents_by_departement


@lru_cache(maxsize=1)
def _load_departements_geojson() -> dict:
    """Charge une seule fois le GeoJSON des départements."""
    with GEOJSON_DEPTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_dataframe_schema(df: pd.DataFrame) -> pd.DataFrame:
    """

    """
    required = {"dept", "accidents"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans df: {missing}")

    # dept en string, avec padding sur 2 chiffres pour les num. métropolitains
    df = df.copy()
    df["dept"] = df["dept"].astype(str)
    df["dept"] = df["dept"].apply(lambda x: x.zfill(2) if x.isdigit() and len(x) < 2 else x)

    if "population" in df.columns:
        # éviter division par zéro
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

    if metric not in df.columns:
        raise ValueError(f"Colonne '{metric}' absente du dataframe.")

    #featureidkey = "properties.code"  

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="dept",              # code département dans df
        color=metric,                  # variable coloriée
        featureidkey=featureidkey,     # clé du GeoJSON qui matche "dept"
        projection="mercator",
        color_continuous_scale="Blues",  # palette
        hover_name="dept",
        labels={
            "accidents": "Accidents",
            "taux_100k": "Taux pour 100 000 hab.",
        },
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(
            title="Valeur",
        ),
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
    Callback Dash : récupère les données et reconstruit la carte.
    A compléter via get_accidents_by_departement(year).
    """
    #  (accidents par département, éventuellement population)
    #df = get_accidents_by_departement(year=year)

    if df is None or len(df) == 0:
        # fig vide mais non plantée
        return px.scatter(title="Aucune donnée disponible")

    df = _ensure_dataframe_schema(df)

    #
    if metric == "taux_100k" and "taux_100k" not in df.columns:
        metric = "accidents"

    return _build_figure(df, metric)
