from __future__ import annotations
from pathlib import Path
import sys

try:
    from .carte import layout as carte_layout
    from ..utils.get_data import query_db
except Exception:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from src.pages.carte import layout as carte_layout
    from src.utils.get_data import query_db

import pandas as pd
import plotly.express as px
from dash import html, dcc

def _make_top_dept_figure(year: int = 2023):
    """Construire un graphique bar des départements les plus impactés (exécution au chargement)."""
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
        return px.bar(title=f"Erreur lecture données: {e}")
    
# ...existing code...

def _get_median_distance_to_radar():
    """Calcule la distance médiane au radar le plus proche"""
    try:
        sql = """
        WITH distances AS (
            SELECT 
                c.acc_id,
                MIN(
                    6371 * 2 * ASIN(
                        SQRT(
                            POW(SIN((r.lat - c.lat_acc) * PI() / 180 / 2), 2) +
                            COS(c.lat_acc * PI() / 180) * COS(r.lat * PI() / 180) *
                            POW(SIN((r.lon - c.lon_acc) * PI() / 180 / 2), 2)
                        )
                    )
                ) as distance_km
            FROM caracteristiques c
            CROSS JOIN radars r
            GROUP BY c.acc_id
        )
        SELECT ROUND(AVG(distance_km), 1) as median_distance
        FROM (
            SELECT distance_km
            FROM distances
            ORDER BY distance_km
            LIMIT 2 - (SELECT COUNT(*) FROM distances) % 2
            OFFSET (SELECT (COUNT(*) - 1) / 2 FROM distances)
        );
        """
        result = query_db(sql)
        if result is None or result.empty:
            return None
        return result.iloc[0]['median_distance']
    except Exception as e:
        print(f"Erreur calcul distance médiane: {e}")
        return None

def _create_kpi_bar():
    """Crée la barre de KPI"""
    median_dist = _get_median_distance_to_radar()
    
    return html.Div([
        html.Div([
            html.H4("Distance médiane au radar le plus proche", 
                   style={'color': '#2c3e50', 'margin': '0'}),
            html.Div([
                html.Span(
                    f"{median_dist:.1f} km" if median_dist else "N/A",
                    style={
                        'fontSize': '24px',
                        'fontWeight': 'bold',
                        'color': '#3498db'
                    }
                )
            ])
        ], style={
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center',
            'margin': '10px'
        })
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'padding': '20px',
        'backgroundColor': '#f8f9fa'
    })

def layout():
    """Page d'accueil : affiche carte + graphiques directement (pas de liens)."""
    bar_fig = _make_top_dept_figure(2023)

    return html.Div([
        # Barre de KPI en haut
        _create_kpi_bar(),
        
        # Reste du layout existant
        html.H1("Dashboard — Accidents et Radars", 
                style={"textAlign": "center", "marginBottom": "8px"}),
        # ...existing code...
    ], style={"padding": "8px"})

    return html.Div(
        [
            html.H1("Dashboard — Accidents et Radars", style={"textAlign": "center", "marginBottom": "8px"}),
            html.P("Vue d'ensemble — carte et statistiques (chargées immédiatement).", style={"textAlign": "center", "marginTop": 0}),
            # inclure la carte (la fonction carte_layout retourne un Div complet)
            carte_layout(),
            # afficher un graphique immédiatement sous la carte
            html.Div(
                [
                    dcc.Graph(id="home-top-dept", figure=bar_fig),
                ],
                style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"},
            ),
        ],
        style={"padding": "8px"},
    )

"""def layout():
    return html.Div(
        [
            html.Section(
                [
                    html.H1("Accidentologie en France", className="hero-title"),
                    html.P(
                        "Explorez les données d'accidents (carte choroplèthe, tendances, indicateurs).",
                        className="hero-subtitle",
                    ),
                    html.Div(
                        [
                            dcc.Link("Voir la carte", href="/carte", className="btn btn-primary"),
                            dcc.Link("En savoir plus", href="/about", className="btn btn-ghost"),
                        ],
                        className="hero-actions",
                    ),
                ],
                className="hero",
            ),

            html.Section(
                [
                    html.Div(
                        [
                            html.H3("Carte choroplèthe"),
                            html.P("Visualisez la distribution des accidents par département."),
                            dcc.Link("Ouvrir la carte →", href="/carte", className="card-link"),
                        ],
                        className="card",
                    ),
                    html.Div(
                        [
                            html.H3("Indicateurs"),
                            html.P("Nombre d'accidents, taux/100k, focus territoriaux."),
                            dcc.Link("Découvrir →", href="/indicateurs", className="card-link", target="_self"),
                        ],
                        className="card",
                    ),
                    html.Div(
                        [
                            html.H3("À propos"),
                            html.P("Sources, méthodologie, limites et pistes d’amélioration."),
                            dcc.Link("Lire →", href="/about", className="card-link"),
                        ],
                        className="card",
                    ),
                ],
                className="cards",
            ),

            html.Footer(
                "© 2025 — Projet d’analyse d’accidentologie",
                className="footer",
            ),
        ],
        className="container",
        style=_base_styles(),
    )

def _base_styles():
    # a revoir
    return {
        "--bg": "#0b1220",
        "--bg-alt": "#0f172a",
        "--panel": "#111827",
        "--text": "#e5e7eb",
        "--muted": "#94a3b8",
        "--accent": "#3b82f6",
        "fontFamily": "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        "color": "var(--text)",
        "background": "linear-gradient(135deg, #0b1220 0%, #0f172a 60%, #111827 100%)",
        "minHeight": "100vh",
        "padding": "0",
        "margin": "0",
    }"""
