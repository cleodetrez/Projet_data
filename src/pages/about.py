from dash import html

def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("À propos"),
                    html.P(
                        "Ce projet présente une exploration de l’accidentologie en France. "
                        "blabkabla"
                    ),
                    html.H3("Sources de données"),
                    html.Ul(
                        [
                            html.Li("Caractéristiques des accidents (caract*.csv)"),
                            html.Li("Localisation des radars"),
                            html.Li("Géométries des départements (GeoJSON)"),
                        ]
                    ),
                    html.H3("Méthodologie (bref)"),
                    html.Ul(
                        [
                            html.Li("Ingestion des CSV, nettoyage, fusion, agrégations par département."),
                            html.Li("Calculs de taux pour 100 000 habitants lorsque la population est disponible."),
                            html.Li("Visualisation via Dash + Plotly."),
                        ]
                    ),
                    html.H3("Limites et améliorations"),
                    html.Ul(
                        [
                            html.Li("Affiner la qualité des géocodages."),
                            html.Li("Ajouter des filtres temporels et par gravité."),
                            html.Li("Documenter les biais de couverture ou de saisie."),
                        ]
                    ),
                ],
                className="prose",
            )
        ],
        className="container",
        style={
            "maxWidth": "960px",
            "margin": "0 auto",
            "padding": "40px 20px",
            "lineHeight": 1.6,
        },
    )
