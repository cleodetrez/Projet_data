"""layout des pages avec barre de navigation et routage dash."""

from __future__ import annotations

from dash import html, dcc, Input, Output, callback

# imports des pages avec repli si le package 'src.' n'est pas utilisé
try:
    from src.pages.home import layout as home_layout
except ImportError:
    from pages.home import layout as home_layout  # type: ignore

try:
    from src.pages.about import layout as about_layout
except ImportError:
    from pages.about import layout as about_layout  # type: ignore

try:
    from src.pages.carte import layout as carte_layout
except ImportError:
    try:
        from pages.carte import layout as carte_layout  # type: ignore
    except ImportError:
        def carte_layout():
            """vue de secours quand la page carte est indisponible."""
            return html.Div("page 'carte' non disponible.", style={"padding": "20px"})


def navbar() -> html.Nav:
    """construit la barre de navigation."""
    return html.Nav(
        [
            html.Div(
                [
                    html.H3(
                        "accidentologie france",
                        style={"color": "white", "marginRight": "32px"},
                    ),
                    dcc.Link("accueil", href="/", className="nav-link"),
                    dcc.Link("carte", href="/carte", className="nav-link"),
                    dcc.Link("à propos", href="/about", className="nav-link"),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "20px",
                    "padding": "10px 20px",
                },
            )
        ],
        style={
            "backgroundColor": "#0f172a",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.2)",
            "position": "sticky",
            "top": 0,
            "zIndex": 1000,
        },
    )


def shell_layout() -> html.Div:
    """layout principal: barre de navigation + conteneur de page."""
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            navbar(),
            html.Div(id="page-content", style={"padding": "24px"}),
        ],
        style={
            # découpé pour respecter 100 caractères/ligne
            "fontFamily": (
                "Inter, system-ui, -apple-system, Segoe UI, Roboto, "
                "sans-serif"
            ),
            "backgroundColor": "#f8fafc",
            "minHeight": "100vh",
        },
    )


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname: str):
    """routeur: renvoie le layout en fonction de l'URL."""
    if pathname in ("/", "", None):
        return home_layout()
    if pathname == "/carte":
        return carte_layout()
    if pathname == "/about":
        return about_layout()
    return html.Div(
        [
            html.H2("404 - page introuvable"),
            html.P(f"chemin demandé : {pathname}"),
        ],
        style={"padding": "40px", "textAlign": "center"},
    )
