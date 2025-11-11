"""
main.py : Point d'entrée principal de l'application.
"""
import sys
from pathlib import Path

# Ajouter la racine du projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Charger les données une seule fois
try:
    from src.utils.get_data import init_db, get_caract_2023, get_radar_2023
    from src.utils.clean_caract_2023 import clean_caract
    from src.utils.clean_radars_2023 import clean_radars
    from src.utils.merge_data import merge_cleaned_year
    
    print("Initialisation de la base de données...")
    init_db()
    get_caract_2023()
    get_radar_2023()
    clean_caract()
    clean_radars()
    merge_cleaned_year(2023, primary_key="Num_Acc")
    print("✓ Base de données prête")
except Exception as e:
    print(f"⚠ Erreur initialisation: {e}")

# Créer l'application Dash
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="src/pages",
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True
)

app.title = "Dashboard Accidents et Radars"

# Layout global simple
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dash.page_container
])

if __name__ == '__main__':
    print("🚀 Lancement du dashboard sur http://127.0.0.1:8050/")
    app.run(debug=True)