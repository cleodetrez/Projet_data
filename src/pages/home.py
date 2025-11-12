from __future__ import annotations
from dash import html, dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
GEOJSON_PATH = ROOT / "departements-version-simplifiee.geojson"

try:
    from ..utils.get_data import query_db
except Exception:
    from src.utils.get_data import query_db


def _make_communes_map():
    """Affiche une carte simple des communes depuis le GeoJSON"""
    try:
        # Charger le GeoJSON
        with GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)
        
        # Créer un dataframe vide avec une colonne pour la coloration
        df = pd.DataFrame({
            "location": ["France"],
            "value": [1]
        })
        
        # Créer la choroplèthe avec le GeoJSON
        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="location",
            color="value",
            featureidkey="properties.nom",
            projection="mercator",
            title="Carte des communes en France",
        )
        
        fig.update_geos(
            center=dict(lon=2, lat=46),  # Centre sur la France
            lataxis_range=[41, 51],
            lonaxis_range=[-6, 8],
        )
        
        fig.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_showscale=False,  # Masquer la barre de couleur
        )
        
        return fig
    
    except Exception as e:
        print(f"Erreur carte communes : {e}")
        # Afficher une carte vide avec message d'erreur
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur : {e}", showarrow=False)
        return fig

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

    # Carte des communes
    html.Div([
        dcc.Graph(id="home-communes-map", figure=_make_communes_map()),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),

    # Histogramme vitesses
    html.Div([
        dcc.Graph(id="home-speed-hist", figure=_make_speed_histogram(2023, bins=40)),
    ], style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"}),
], style={"padding": "8px"})