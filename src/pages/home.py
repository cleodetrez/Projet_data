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
    
def _make_speed_histogram(year: int = 2023, bins: int = 30):
    """
    Histogramme du nombre des différentes vitesses mesurées.
    Utilise la table 'radars' et la colonne 'mesure'.
    Filtre sur l'année si la colonne 'annee' ou 'datetime' existe.
    """
    try:
        sql = """
        SELECT mesure AS speed, annee, datetime
        FROM radars
        WHERE mesure IS NOT NULL
          AND (
                annee = :year
                OR (datetime IS NOT NULL AND strftime('%Y', datetime) = :year_str)
              )
        """
        df = query_db(sql, {"year": year, "year_str": str(year)})
        if df is None or df.empty:
            return px.histogram(title="Aucune mesure de vitesse disponible")
        df["speed"] = pd.to_numeric(df["speed"], errors="coerce")
        df = df.dropna(subset=["speed"])
        if df.empty:
            return px.histogram(title="Aucune mesure de vitesse numérique")
        fig = px.histogram(df, x="speed", nbins=bins,
                           title=f"Distribution des vitesses mesurées ({year})",
                           labels={"speed": "Vitesse (km/h)", "count": "Nombre de mesures"})
        fig.update_layout(bargap=0.05, template="plotly_white")
        return fig
    except Exception as e:
        return px.histogram(title=f"Erreur génération histogramme: {e}")

def _get_median_distance_to_radar():
    return None

def _create_kpi_bar():
    return html.Div()

def layout():
    """Page d'accueil : affiche carte + graphiques directement (pas de liens)."""
    bar_fig = _make_top_dept_figure(2023)
    speed_fig = _make_speed_histogram(2023, bins=40)

    return html.Div(
        [
            html.H1("Dashboard — Accidents et Radars", style={"textAlign": "center", "marginBottom": "8px"}),
            html.P("Vue d'ensemble — carte et statistiques (chargées immédiatement).", style={"textAlign": "center", "marginTop": 0}),

            # Carte (déjà définie dans src/pages/carte.py)
            carte_layout(),

            # Histogramme des vitesses
            html.Div(
                [
                    dcc.Graph(id="home-speed-hist", figure=speed_fig),
                ],
                style={"maxWidth": "1100px", "margin": "24px auto", "padding": "12px"},
            ),

            # Top departments bar
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
