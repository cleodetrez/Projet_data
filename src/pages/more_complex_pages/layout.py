"""

"""

from dash import html, dcc, Input, Output, callback

from src.pages.home import layout as home_layout
from src.pages.about import layout as about_layout

try:
    from src.pages.carte import layout as carte_layout
except Exception:
    def carte_layout():
        return html.Div("Page 'Carte' non disponible.", style={"padding": "20px"})

def navbar():
    return html.Nav(
        [
            html.Div(
                [
                    html.H3("Accidentologie France", style={"color": "white", "marginRight": "32px"}),
                    dcc.Link("Accueil", href="/", className="nav-link"),
                    dcc.Link("Carte", href="/carte", className="nav-link"),
                    dcc.Link("À propos", href="/about", className="nav-link"),
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

def shell_layout():
    """Layout principal affichant la barre de navigation + contenu."""
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            navbar(),
            html.Div(id="page-content", style={"padding": "24px"}),
        ],
        style={
            "fontFamily": "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
            "backgroundColor": "#f8fafc",
            "minHeight": "100vh",
        },
    )

@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    """Routeur : affiche la page correspondant à l'URL."""
    if pathname in ("/", "", None):
        return home_layout()
    elif pathname == "/carte":
        return carte_layout()
    elif pathname == "/about":
        return about_layout()
    else:
        return html.Div(
            [
                html.H2("404 - Page introuvable"),
                html.P(f"Chemin demandé : {pathname}"),
            ],
            style={"padding": "40px", "textAlign": "center"},
        )