"""routage des pages dash (layout global + callbacks)."""

from __future__ import annotations

from dash import html, dcc, Input, Output, callback

# navbar
try:
    from src.pages.navbar import navbar  # si l'appli est lancée en package
except ImportError:
    from pages.navbar import navbar  # repli en import relatif

# pages : home
try:
    from src.pages.home import layout as home_layout
except ImportError:
    from pages.home import layout as home_layout

# pages : about
try:
    from src.pages.about import layout as about_layout
except ImportError:
    from pages.about import layout as about_layout

# pages : carte (avec repli si absente)
try:
    from src.pages.carte import layout as map_layout
except ImportError:
    try:
        from pages.carte import layout as map_layout
    except ImportError:
        def map_layout():
            """vue de repli si la page carte est indisponible."""
            return html.Div("la page est indisponible", style={"padding": "20px"})


def shell_layout():
    """layout global : barre de nav + zone de contenu + dcc.Location."""
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
    """retourne le layout correspondant au chemin demandé."""
    if pathname in ("/", "", None):
        return home_layout()
    if pathname == "/about":
        return about_layout()
    if pathname == "/carte":
        return map_layout()
    # 404
    return html.Div(
        [
            html.H2("404 — page introuvable"),
            html.P(f"chemin demandé : {pathname}"),
        ],
        style={"maxWidth": "800px", "margin": "40px auto"},
    )
