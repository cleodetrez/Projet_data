from dash import html, dcc

def navbar():
    return html.Nav(
        [
            html.Div(
                [
                    dcc.Link("Mon Dashboard", href="/", className="brand"),
                    html.Div(
                        [
                            dcc.Link("Accueil", href="/", className="nav-link"),
                            dcc.Link("Carte", href="/carte", className="nav-link"),
                            dcc.Link("About", href="/about", className="nav-link"),
                        ],
                        className="nav-items",
                    ),
                ],
                className="nav-inner",
            )
        ],
        style={"backgroundColor": "#0f172a"},
        className="navbar",
    )
