"""layout des pages avec barre de navigation et routage dash."""

from __future__ import annotations

from dash import html, dcc, Input, Output, callback

# résolution des layouts avec imports groupés et repli
try:
    from src.pages import home as _home, about as _about, carte as _carte  # type: ignore
    home_layout = _home.layout
    about_layout = _about.layout
    carte_layout = _carte.layout  # type: ignore[attr-defined]
except ImportError:
    try:
        from pages import home as _home, about as _about, carte as _carte  # type: ignore
        home_layout = _home.layout
        about_layout = _about.layout
        carte_layout = _carte.layout  # type: ignore[attr-defined]
    except ImportError:
        def carte_layout() -> html.Div:
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
            "fontFamily": (
                "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
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
