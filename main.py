import logging
from dash import Dash, html, dcc, Output, Input
from src.utils.get_data import get_caract_2023, get_radar_2023
from src.utils.clean_caract_2023 import clean_caract
from src.utils.clean_radars_2023 import clean_radars
from src.utils.merge_data import merge_cleaned_year
from src.pages.setup import render_setup_page, STEP_FLOW
from src.pages.home import layout as home_layout

# Config du logging
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
        log_messages.append("[STEP] Téléchargement du CSV")
        get_caract_2023()
        get_radar_2023()

        log_messages.append("[STEP] Initialisation de la base SQLite")
        df_caract_clean = clean_caract()
        df_radars_clean = clean_radars()

        log_messages.append("[STEP] Vérification des données")
        merge_cleaned_year(None, primary_key='acc_id')

        log_messages.append("[STEP] Initialisation terminée")
        return True
    except Exception as e:
        logger.error(f"Erreur dans la pipeline: {e}")
        log_messages.append(str(e))
        return False

# Initialisation de l'application Dash
app = Dash(__name__)
log_messages = []
progress_step = 0
success = False
completed = False

app.layout = html.Div([
    dcc.Interval(id="interval-loader", interval=1500, n_intervals=0, disabled=False),
    html.Div(id="page-content")
])


# Callback : loader + dashboard

@app.callback(
    Output("page-content", "children"),
    Output("interval-loader", "disabled"),
    Input("interval-loader", "n_intervals")
)
def update_loader(n):
    global progress_step, success, completed

    if not completed:
        if progress_step < len(STEP_FLOW):
            step = STEP_FLOW[progress_step]
            log_messages.append(f"[STEP] {step}")
            progress_step += 1
            return render_setup_page(log_messages, step, completed=False, success=False), False
        else:
            success = run_data_pipeline(log_messages)
            completed = True
            return render_setup_page(log_messages, "Initialisation terminée", completed=True, success=success), True
    else:
        if success:
            return home_layout, True
        else:
            return html.Div("Erreur : l'initialisation a échoué.", style={"color": "red"}), True


if __name__ == "__main__":
    app.run(debug=True)
