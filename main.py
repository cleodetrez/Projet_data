"""
main.py : Point d'entrée principal de l'application.

Usage:
  python main.py --pipeline  # Exécute le pipeline de données (téléchargement/nettoyage)
  python main.py --dash     # Lance le dashboard (utilise les données nettoyées)
  python main.py           # Lance uniquement le dashboard
"""
import logging
import threading
import sys
from typing import Dict, Any
from pathlib import Path
import argparse

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
    "started": False,   # évite plusieurs lancements
}

def _push_step(label: str) -> None:
    STATE["current_step"] = label
    STATE["messages"].append(f"[STEP] {label}")
    logger.info(label)

def check_clean_files_exist() -> bool:
    """Vérifie si les fichiers de données nettoyées existent."""
    clean_dir = Path(__file__).parent / "data" / "cleaned"
    required_files = ["caract_clean.csv", "radars_delta_clean.csv"]
    missing = [f for f in required_files if not (clean_dir / f).exists()]
    if missing:
        logger.warning("Fichiers manquants: %s", ", ".join(missing))
        return False
    return True

def run_data_pipeline() -> None:
    try:
        # 1) Téléchargements / lecture
        _push_step("Téléchargement du CSV")
        get_caract_2023()
        get_radar_2023()

        # 2) Nettoyages
        _push_step("Initialisation de la base SQLite")
        try:
            df_caract_clean = clean_caract()
            df_radars_clean = clean_radars()
        except Exception as e:
            logger.error("Erreur pendant le nettoyage : %s", e)
            raise
        logger.info("Nettoyages: %s accidents, %s radars",
                    len(df_caract_clean) if df_caract_clean is not None else "NA",
                    len(df_radars_clean) if df_radars_clean is not None else "NA")

        # 3) Vérifications / fusion
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
    # On interroge l'état toutes les 2 secondes
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
        # Call home_layout() instead of returning the function reference
        return home_layout(), True
    else:
        return html.Div(
            [
                html.H2("Une erreur est survenue pendant l'initialisation."),
                html.Pre("\n".join(STATE["messages"][-10:])),
            ],
            style={"maxWidth": "800px", "margin": "40px auto", "fontFamily": "Arial"},
        ), True


def main(run_pipeline: bool = False, run_dash: bool = True):
    """Point d'entrée principal."""
    if run_pipeline:
        logger.info("Démarrage synchrone du pipeline de données...")
        STATE["started"] = True
        run_data_pipeline()
        if not STATE["success"]:
            logger.error("Pipeline échoué. Voir les logs pour plus de détails.")
            sys.exit(1)
        logger.info("Pipeline terminé avec succès.")

    if run_dash:
        # Ne bloque pas le démarrage du dashboard si les fichiers nettoyés manquent :
        if not check_clean_files_exist() and not run_pipeline:
            logger.warning("Fichiers nettoyés absents — le pipeline sera lancé en arrière-plan.")
            STATE["started"] = True
            threading.Thread(target=run_data_pipeline, daemon=True).start()

        logger.info("Démarrage du dashboard...")
        # app.run_server est obsolète -> utiliser app.run
        app.run(debug=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application d'analyse d'accidentologie")
    parser.add_argument("--pipeline", action="store_true", help="Exécute le pipeline de données")
    parser.add_argument("--dash", action="store_true", help="Lance le dashboard")
    args = parser.parse_args()
    
    # Si aucun argument, lance juste le dashboard
    if not (args.pipeline or args.dash):
        args.dash = True
    
    main(run_pipeline=args.pipeline, run_dash=args.dash)
