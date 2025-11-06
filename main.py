# main.py
import logging
import threading
from typing import Dict, Any

from dash import Dash, html, dcc, Output, Input

from src.utils.get_data import get_caract_2023, get_radar_2023
from src.utils.clean_caract_2023 import clean_caract
from src.utils.clean_radars_2023 import clean_radars
from src.utils.merge_data import merge_cleaned_year
from src.pages.setup import render_setup_page, STEP_FLOW
from src.pages.home import layout as home_layout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

STATE: Dict[str, Any] = {
    "messages": [],
    "current_step": None,
    "completed": False,
    "success": False,
    "started": False,   
}

def _push_step(label: str) -> None:
    STATE["current_step"] = label
    STATE["messages"].append(f"[STEP] {label}")
    logger.info(label)

def run_data_pipeline() -> None:
    try:
        _push_step("Téléchargement du CSV")
        get_caract_2023()
        get_radar_2023()

        _push_step("Initialisation de la base SQLite")
        df_caract_clean = clean_caract()
        df_radars_clean = clean_radars()
        logger.info("Nettoyages: %s accidents, %s radars",
                    len(df_caract_clean) if df_caract_clean is not None else "NA",
                    len(df_radars_clean) if df_radars_clean is not None else "NA")

        _push_step("Vérification des données")
        merge_cleaned_year(None, primary_key="acc_id")

        _push_step("Initialisation terminée")
        STATE["success"] = True
    except Exception as e:
        logger.exception("Erreur dans la pipeline: %s", e)
        STATE["messages"].append(str(e))
        STATE["success"] = False
    finally:
        STATE["completed"] = True


app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Interval(id="tick", interval=2000, n_intervals=0, disabled=False),
    html.Div(id="page-content")
])


@app.callback(
    Output("page-content", "children"),
    Output("tick", "disabled"),
    Input("tick", "n_intervals"),
)
def render_page(_):
    if not STATE["started"]:
        STATE["started"] = True
        threading.Thread(target=run_data_pipeline, daemon=True).start()

    if not STATE["completed"]:
        return (
            render_setup_page(
                messages=STATE["messages"],
                current_step=STATE["current_step"],
                completed=False,
                success=False,
            ),
            False,  
        )

    if STATE["success"]:
        return home_layout, True
    else:
        return html.Div(
            [
                html.H2("Une erreur est survenue pendant l'initialisation."),
                html.Pre("\n".join(STATE["messages"][-10:])),
            ],
            style={"maxWidth": "800px", "margin": "40px auto", "fontFamily": "Arial"},
        ), True


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
