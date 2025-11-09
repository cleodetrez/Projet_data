"""
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from dash import html, dcc, Input, Output, callback

from src.pages.barrenavigation import navbar
from src.pages.home import layout as home_layout
from src.pages.about import layout as about_layout

try:
    from src.pages.carte import layout as map_layout
except Exception:
    def map_layout():
        return html.Div("la page est indispo", style={"padding": "20px"})

def shell_layout():
    """layout global: barre de nav + slot pour les pages + Location pour le routage."""
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            navbar(),
            html.Div(id="route-content", style={"padding": "24px"}),
        ]
    )

@callback(
    Output("route-content", "children"),
    Input("url", "pathname"),
)
def router(pathname: str):
    if pathname in ("/", "", None):
        return home_layout()
    if pathname == "/about":
        return about_layout()
    if pathname == "/carte":
        return map_layout()
    # 404
    return html.Div(
        [
            html.H2("404 — Page introuvable"),
            html.P(f"Chemin demandé : {pathname}"),
        ],
        style={"maxWidth": "800px", "margin": "40px auto"},
    )
