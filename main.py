"""point d'entrée dash minimal."""

from dash import Dash, html
from src.pages.home import layout as home_layout


app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # utile pour le déploiement (gunicorn, etc.)
app.layout = home_layout  # home_layout est déjà un composant html.Div

if __name__ == "__main__":
    print("dashboard sur http://127.0.0.1:8050/")
    app.run(debug=True, port=8050)
