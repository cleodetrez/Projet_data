import logging
from src.utils.get_data import get_caract_2023, get_radar_2023
from src.utils.clean_caract_2023 import clean_caract
from src.utils.clean_radars_2023 import clean_radars
from src.utils.merge_data import merge_cleaned_year
from src.pages.setup import render_setup_page, STEP_FLOW
from src.pages.home import layout as home_layout


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_data_pipeline(log_messages):
    """
    Simule le chargement des données avec logs pour le loader.
    """
    try:
        # Étape 1 : Téléchargement
        log_messages.append("[STEP] Téléchargement du CSV")
        get_caract_2023()
        get_radar_2023()

        # Étape 2 : Nettoyage
        log_messages.append("[STEP] Initialisation de la base SQLite")
        df_caract_clean = clean_caract()
        df_radars_clean = clean_radars()

        # Étape 3 : Fusion
        log_messages.append("[STEP] Vérification des données")
        merge_cleaned_year(None, primary_key='acc_id')

        log_messages.append("[STEP] Initialisation terminée")
        return True  # succès
    except Exception as e:
        logger.error(f"Erreur dans la pipeline: {e}")
        log_messages.append(str(e))
        return False

#dashboard
from dash import Dash, html, dcc, Output, Input

app = Dash(__name__)
log_messages = []

app.layout = html.Div([
    dcc.Interval(id="interval-loader", interval=1000, n_intervals=0),
    html.Div(id="page-content")
])

# variable globale pour simuler la progression
progress_step = 0
success = False
completed = False

@app.callback(
    Output("page-content", "children"),
    Input("interval-loader", "n_intervals")
)
def update_loader(n):
    global progress_step, success, completed

    # Si le traitement n'est pas terminé, on affiche le loader
    if not completed:
        if progress_step < len(STEP_FLOW):
            step = STEP_FLOW[progress_step]
            log_messages.append(f"[STEP] {step}")
            progress_step += 1
            return render_setup_page(log_messages, step, completed=False, success=False)
        else:
            # Lance la vraie préparation (tu peux le faire en thread si long)
            success = run_data_pipeline(log_messages)
            completed = True
            return render_setup_page(log_messages, "Initialisation terminée", completed=True, success=success)
    else:
        # Si c'est fini → afficher la page principale
        if success:
            return home_layout
        else:
            return html.Div("Erreur : l'initialisation a échoué.", style={"color": "red"})



if __name__ == "__main__":
    app.run(debug=True)
