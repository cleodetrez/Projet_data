"""page à propos pour l'application dash."""

from dash import html


def layout():
    """retourne le layout de la page."""
    return html.Div(
        [
            html.H2(
                "À Propos",
                style={
                    "paddingBottom": "10px",
                },
            ),
            html.Div(
                [
                    html.P(
                        [
                            html.Span(
                                "▸ ",
                                style={
                                    "color": "#f093fb",
                                    "fontWeight": "bold",
                                    "marginRight": "8px",
                                },
                            ),
                            "Ce dashboard analyse les accidents de la circulation routière "
                            "et les vitesses relevées par radars en France (2020-2024)."
                        ],
                        style={"fontSize": "16px", "lineHeight": "1.8", "marginBottom": "20px"},
                    ),
                    html.P(
                        [
                            html.Span(
                                "▸ ",
                                style={
                                    "color": "#00d4ff",
                                    "fontWeight": "bold",
                                    "marginRight": "8px",
                                },
                            ),
                            "Il permet de visualiser l'évolution de l'accidentologie à travers "
                            "des cartes interactives, des graphiques temporels et des statistiques "
                            "détaillées par département, commune et région."
                        ],
                        style={"fontSize": "16px", "lineHeight": "1.8", "marginBottom": "20px"},
                    ),
                    html.P(
                        [
                            html.Span(
                                "▸ ",
                                style={
                                    "color": "#f093fb",
                                    "fontWeight": "bold",
                                    "marginRight": "8px",
                                },
                            ),
                            "Réalisé en 2025 dans le cadre d'un projet d'école d'ingénieur, "
                            "cet outil vise à faciliter l'exploration et la compréhension des "
                            "données d'accidentologie en France."
                        ],
                        style={"fontSize": "16px", "lineHeight": "1.8", "marginBottom": "20px"},
                    ),
                    html.P(
                        [
                            html.Span(
                                "▸ ",
                                style={
                                    "color": "#00d4ff",
                                    "fontWeight": "bold",
                                    "marginRight": "8px",
                                },
                            ),
                            "Il permet d'identifier les zones à risque, d'analyser les facteurs "
                            "d'accidents et de suivre l'impact des politiques de sécurité routière."
                        ],
                        style={"fontSize": "16px", "lineHeight": "1.8"},
                    ),
                ],
                className="page-card",
                style={"padding": "24px"},
            ),
        ]
    )
