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

def _make_top_dept_figure(year: int = 2023):
    """Top 10 départements"""
    try:
        sql = """
        SELECT dep AS dept, COUNT(*) AS accidents
        FROM caracteristiques
        WHERE annee = :year
        GROUP BY dep
        ORDER BY accidents DESC
        LIMIT 10
        """
        df = query_db(sql, {"year": year})
        if df is None or df.empty:
            return px.bar(title="Aucune donnée disponible")
        return px.bar(df, x="dept", y="accidents", title=f"Top 10 départements ({year})")
    except Exception as e:
        return px.bar(title=f"Erreur: {e}")

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
                           title=f"Distribution des vitesses")
        fig.update_layout(bargap=0.05)
        return fig
    except Exception as e:
        return px.histogram(title=f"Erreur: {e}")

# Layout principal
layout = html.Div([
    html.H1("Dashboard — Accidents et Radars", style={"textAlign": "center", "marginBottom": "8px"}),
    html.P("Vue d'ensemble", style={"textAlign": "center"}),
    
    # Histogramme vitesses
    html.Div([
        dcc.Graph(id="home-speed-hist", figure=_make_speed_histogram(2023, bins=40)),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),

    # Top departments bar
    html.Div([
        dcc.Graph(id="home-top-dept", figure=_make_top_dept_figure(2023)),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),
], style={"padding": "8px"})