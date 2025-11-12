from __future__ import annotations
import dash
from dash import html, dcc, callback, Input, Output
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


# ============================================================================
# Composants des pages
# ============================================================================

def _make_departments_choropleth():
    """Carte choroplèthe par département"""
    try:
        with GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)
        
        # Charger les données d'accidents par département
        sql = "SELECT dep AS dept, COUNT(*) AS accidents FROM caracteristiques GROUP BY dep"
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        df["dept"] = df["dept"].astype(str).str.zfill(2)
        
        # Créer la choroplèthe
        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="dept",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale="Blues",
            title="Accidentologie par département (France)",
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            template="plotly_white",
        )
        
        return fig
    
    except Exception as e:
        print(f"Erreur carte : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur : {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


def _make_speed_histogram():
    """Histogramme vitesses"""
    try:
        sql = "SELECT mesure AS speed FROM radars WHERE mesure IS NOT NULL LIMIT 5000"
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        df["speed"] = pd.to_numeric(df["speed"], errors="coerce")
        df = df.dropna(subset=["speed"])
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Pas de données", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = px.histogram(
            df, 
            x="speed", 
            nbins=40,
            title="Distribution des vitesses mesurées (2023)",
            labels={"speed": "Vitesse (km/h)"}
        )
        fig.update_layout(bargap=0.05, height=500)
        return fig
    
    except Exception as e:
        print(f"Erreur histogramme : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur: {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


def _make_accidents_by_hour():
    """Graphique accidents par heure"""
    try:
        sql = "SELECT heure FROM caracteristiques WHERE heure IS NOT NULL"
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        df["heure"] = pd.to_numeric(df["heure"], errors="coerce")
        df = df.dropna(subset=["heure"])
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Pas de données", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = px.histogram(
            df,
            x="heure",
            nbins=24,
            title="Accidents par heure du jour (2023)",
            labels={"heure": "Heure (0-23)"}
        )
        fig.update_layout(bargap=0.05, height=500)
        return fig
    
    except Exception as e:
        print(f"Erreur graphique : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur: {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


# ============================================================================
# Pages de contenu
# ============================================================================

about_page = html.Div([
    html.H2("À propos", style={"color": "#2c3e50", "borderBottom": "3px solid #3498db", "paddingBottom": "10px"}),
    html.Div([
        html.P("Ce dashboard analyse les accidents de la circulation routière et les vitesses relevées par radars en France (2023).", style={"fontSize": "16px", "lineHeight": "1.6"}),
        html.P("Les données proviennent de sources publiques (data.gouv.fr) et permettent une visualisation complète de l'accidentologie française.", style={"fontSize": "16px", "lineHeight": "1.6"}),
        html.P("Sources : data.gouv.fr - Données publiques", style={"fontSize": "14px", "color": "#7f8c8d", "marginTop": "20px"}),
    ], style={
        "backgroundColor": "white",
        "padding": "24px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    })
])

histogram_page = html.Div([
    html.H2("Distribution des vitesses", style={"color": "#2c3e50", "borderBottom": "3px solid #3498db", "paddingBottom": "10px"}),
    html.Div([
        dcc.Graph(figure=_make_speed_histogram()),
    ], style={
        "backgroundColor": "white",
        "padding": "24px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    })
])

choropleth_page = html.Div([
    html.H2("Carte choroplèthe des accidents", style={"color": "#2c3e50", "borderBottom": "3px solid #3498db", "paddingBottom": "10px"}),
    html.Div([
        dcc.Graph(figure=_make_departments_choropleth()),
    ], style={
        "backgroundColor": "white",
        "padding": "24px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    })
])

graph_page = html.Div([
    html.H2("Accidents par heure", style={"color": "#2c3e50", "borderBottom": "3px solid #3498db", "paddingBottom": "10px"}),
    html.Div([
        dcc.Graph(figure=_make_accidents_by_hour()),
    ], style={
        "backgroundColor": "white",
        "padding": "24px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    })
])

authors_page = html.Div([
    html.H2("Auteurs", style={"color": "#2c3e50", "borderBottom": "3px solid #3498db", "paddingBottom": "10px"}),
    html.Div([
        html.P("Projet d'analyse d'accidentologie routière", style={"fontSize": "16px", "lineHeight": "1.6"}),
        html.P("2025", style={"fontSize": "16px", "lineHeight": "1.6"}),
        html.Hr(),
        html.P("Développé avec Dash, Plotly et SQLite", style={"fontSize": "14px", "color": "#7f8c8d"}),
    ], style={
        "backgroundColor": "white",
        "padding": "24px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    })
])


# ============================================================================
# Barre de navigation
# ============================================================================

def create_nav_button(label, button_id, active=False):
    """Crée un bouton de navigation stylisé"""
    return html.Button(
        label,
        id=button_id,
        n_clicks=0,
        style={
            "padding": "12px 24px",
            "margin": "0 5px",
            "fontSize": "15px",
            "fontWeight": "500",
            "cursor": "pointer",
            "border": "none",
            "borderRadius": "4px",
            "backgroundColor": "#3498db" if active else "transparent",
            "color": "white",
            "transition": "all 0.3s ease",
        },
        className="nav-button"
    )

navbar = html.Div([
    html.Div([
        html.Div([
            html.H3("📊 Dashboard", style={"color": "white", "margin": "0 20px 0 0"}),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            create_nav_button("About", "btn-about"),
            create_nav_button("Histogramme", "btn-histogram"),
            create_nav_button("Carte Choroplèthe", "btn-choropleth"),
            create_nav_button("Graphique", "btn-graph"),
            create_nav_button("Auteurs", "btn-authors"),
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "gap": "10px",
            "flex": "1",
        }),
        html.Div(style={"width": "120px"}),  # Espace pour équilibre
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "0 20px",
        "backgroundColor": "#2c3e50",
        "minHeight": "70px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
    })
], id="navbar", style={
    "position": "sticky",
    "top": "0",
    "zIndex": "1000",
})


# ============================================================================
# Layout principal avec callback
# ============================================================================

layout = html.Div([
    navbar,
    html.Div(id="page-content", style={
        "padding": "30px 20px",
        "maxWidth": "1200px",
        "margin": "0 auto",
    }),
], style={
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "backgroundColor": "#f8f9fa",
    "minHeight": "100vh",
})


# Callback pour afficher le contenu de la page
@callback(
    Output("page-content", "children"),
    [
        Input("btn-about", "n_clicks"),
        Input("btn-histogram", "n_clicks"),
        Input("btn-choropleth", "n_clicks"),
        Input("btn-graph", "n_clicks"),
        Input("btn-authors", "n_clicks"),
    ]
)
def display_page(about_clicks, hist_clicks, chor_clicks, graph_clicks, auth_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return about_page
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "btn-about":
        return about_page
    elif button_id == "btn-histogram":
        return histogram_page
    elif button_id == "btn-choropleth":
        return choropleth_page
    elif button_id == "btn-graph":
        return graph_page
    elif button_id == "btn-authors":
        return authors_page
    
    return about_page