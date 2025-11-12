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

# Importe les fonctions nécessaires de carte.py
from src.pages.carte import _build_figure, _ensure_dataframe_schema

def _make_choropleth_map(year: int = 2023, metric: str = "accidents"):
    """Carte choroplèthe par département (réutilise la logique de carte.py)"""
    try:
        sql = """
        SELECT dep AS dept, COUNT(*) AS accidents
        FROM caracteristiques
        WHERE annee = :year OR (annee IS NULL AND :year IS NULL)
        GROUP BY dep
        """
        df = query_db(sql, {"year": year})
    except Exception as e:
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

    # Carte choroplèthe par département (importée de carte.py)
    html.Div([
        dcc.Graph(id="home-choropleth-map", figure=_make_choropleth_map(2023, metric="accidents")),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),

    # Histogramme vitesses
    html.Div([
        dcc.Graph(id="home-speed-hist", figure=_make_speed_histogram(2023, bins=40)),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),
], style={"padding": "8px"})