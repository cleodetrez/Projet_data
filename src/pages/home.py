from __future__ import annotations
import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

# Enregistrer la page
dash.register_page(__name__, path="/")

try:
    from ..utils.get_data import query_db
except Exception:
    from src.utils.get_data import query_db

def _make_accidents_map(year: int = 2023, limit: int = 1000):
    """Carte des accidents localisés (scatter mapbox)"""
    try:
        sql = f"""
        SELECT lat, lon
        FROM caracteristiques
        WHERE annee = :year
          AND lat IS NOT NULL AND lon IS NOT NULL
        LIMIT {limit}
        """
        df = query_db(sql, {"year": year})
        if df is None or df.empty:
            return px.scatter_mapbox(title="Aucune donnée géolocalisée")
        df = df.dropna(subset=["lat", "lon"])
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            zoom=5,
            height=500,
            title=f"Localisation des accidents ({len(df)} points, {year})",
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        return fig
    except Exception as e:
        return px.scatter_mapbox(title=f"Erreur: {e}")

def _make_speed_histogram(year: int = 2023, bins: int = 30):
    """Histogramme vitesses"""
    try:
        sql = """
        SELECT mesure AS speed FROM radars
        WHERE mesure IS NOT NULL LIMIT 5000
        """
        df = query_db(sql)
        if df is None or df.empty:
            return px.histogram(title="Aucune donnée")
        df["speed"] = pd.to_numeric(df["speed"], errors="coerce")
        df = df.dropna(subset=["speed"])
        if df.empty:
            return px.histogram(title="Pas de données")
        fig = px.histogram(df, x="speed", nbins=bins,
                           title=f"Distribution des vitesses en 2023")
        fig.update_layout(bargap=0.05)
        return fig
    except Exception as e:
        return px.histogram(title=f"Erreur: {e}")

# Layout principal
layout = html.Div([
    html.H1("Dashboard — Accidents et Radars", style={"textAlign": "center", "marginBottom": "8px"}),
    html.P("Vue d'ensemble", style={"textAlign": "center"}),

    # Carte des accidents
    html.Div([
        dcc.Graph(id="home-accidents-map", figure=_make_accidents_map(2023, limit=1000)),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),

    # Histogramme vitesses
    html.Div([
        dcc.Graph(id="home-speed-hist", figure=_make_speed_histogram(2023, bins=40)),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),
], style={"padding": "8px"})