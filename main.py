"""point d'entrée dash : setup + lancement complet."""

import sys
import logging
from pathlib import Path
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent

# ============================================================================
# Setup initial (données, nettoyage, DB)
# ============================================================================

def setup_data():
    """Télécharge, nettoie et charge tout dans la DB."""
    logger.info("Initialisation des données...")
    
    try:
        # Imports locaux
        from src.utils.clean_caract_2020 import clean_caracteristiques as clean_2020
        from src.utils.clean_caract_2021 import clean_caracteristiques as clean_2021
        from src.utils.clean_caract_2022 import clean_caracteristiques as clean_2022
        from src.utils.clean_caract_2023 import clean_caracteristiques as clean_2023
        from src.utils.clean_caract_2024 import clean_caracteristiques as clean_2024
        from load_to_db import load_csv_to_db
        
        cleaners = {
            2020: clean_2020,
            2021: clean_2021,
            2022: clean_2022,
            2023: clean_2023,
            2024: clean_2024,
        }
        
        # Nettoyer par année
        for year, cleaner in cleaners.items():
            cleaned_path = ROOT / "data" / "cleaned" / f"caract_clean_{year}.csv"
            if cleaned_path.exists():
                logger.info(f"✓ caract_clean_{year}.csv existe déjà")
            else:
                logger.info(f"🧹 Nettoyage {year}...")
                try:
                    cleaner()
                except Exception as e:
                    logger.warning(f"Erreur nettoyage {year}: {e}")
        
        # Charger tout dans la DB
        logger.info("Chargement en base de données...")
        load_csv_to_db()
        logger.info("Données prêtes!")
        
    except Exception as e:
        logger.error(f"Erreur setup données: {e}")
        sys.exit(1)


# ============================================================================
# Dash app
# ============================================================================

from dash import Dash
from src.pages.home import layout as home_layout


app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.layout = home_layout


if __name__ == "__main__":
    # Setup données une fois au démarrage (pas en debug reload)
    import os
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        setup_data()
    
    logger.info("Dashboard sur http://127.0.0.1:8050/")
    app.run(debug=True, port=8050)