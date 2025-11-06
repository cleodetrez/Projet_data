from dash import html, dcc

def layout():
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
    }
