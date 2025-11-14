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
    logger.info(" Initialisation des données...")
    
    try:
        # Imports locaux - Caractéristiques
        from src.utils.get_data import (
            get_caract_2020, get_caract_2021, get_caract_2022, 
            get_caract_2023, get_caract_2024,
            get_radar_2021, get_radar_2023
        )
        from src.utils.clean_caract_2020 import clean_caracteristiques as clean_caract_2020
        from src.utils.clean_caract_2021 import clean_caracteristiques as clean_caract_2021
        from src.utils.clean_caract_2022 import clean_caracteristiques as clean_caract_2022
        from src.utils.clean_caract_2023 import clean_caracteristiques as clean_caract_2023
        from src.utils.clean_caract_2024 import clean_caracteristiques as clean_caract_2024
        
        # Imports locaux - Radars
        from src.utils.clean_radars_2021 import clean_radars as clean_radars_2021
        from src.utils.clean_radars_2023 import clean_radars as clean_radars_2023
        
        from load_to_db import load_csv_to_db
        
        caract_getters = {
            2020: get_caract_2020,
            2021: get_caract_2021,
            2022: get_caract_2022,
            2023: get_caract_2023,
            2024: get_caract_2024,
        }
        
        caract_cleaners = {
            2020: clean_caract_2020,
            2021: clean_caract_2021,
            2022: clean_caract_2022,
            2023: clean_caract_2023,
            2024: clean_caract_2024,
        }
        
        radar_getters = {
            2021: get_radar_2021,
            2023: get_radar_2023,
        }
        
        radar_cleaners = {
            2021: clean_radars_2021,
            2023: clean_radars_2023,
        }
        
        # ============ Nettoyer CARACTÉRISTIQUES (5 années) ============
        logger.info("Traitement CARACTÉRISTIQUES...")
        for year in caract_cleaners.keys():
            cleaned_path = ROOT / "data" / "cleaned" / f"caract_clean_{year}.csv"
            raw_path = ROOT / "data" / "raw" / f"caracteristiques-{year}.csv"
            
            if cleaned_path.exists():
                logger.info(f"  ✓ caract_clean_{year}.csv existe déjà")
                continue
            
            if not raw_path.exists():
                logger.info(f"  ↓ Téléchargement caracteristiques-{year}.csv...")
                try:
                    caract_getters[year]()
                    logger.info(f"  ✓ Téléchargement {year} terminé")
                except Exception as e:
                    logger.error(f" Erreur téléchargement caract {year}: {e}")
                    continue
            
            logger.info(f" Nettoyage caract {year}...")
            try:
                caract_cleaners[year]()
                logger.info(f"  ✓ Nettoyage caract {year} terminé")
            except Exception as e:
                logger.error(f" Erreur nettoyage caract {year}: {e}")
        
        # ============ Nettoyer RADARS (2 années) ============
        logger.info("Traitement RADARS...")
        for year in radar_cleaners.keys():
            cleaned_path = ROOT / "data" / "cleaned" / f"radars_delta_clean_{year}.csv"
            raw_path = ROOT / "data" / "raw" / f"radars-{year}.csv"
            
            if cleaned_path.exists():
                logger.info(f"  ✓ radars_delta_clean_{year}.csv existe déjà")
                continue
            
            if not raw_path.exists():
                logger.info(f"  ↓ Téléchargement radars-{year}.csv...")
                try:
                    radar_getters[year]()
                    logger.info(f"  ✓ Téléchargement radars {year} terminé")
                except Exception as e:
                    logger.error(f" Erreur téléchargement radars {year}: {e}")
                    continue
            
            logger.info(f" Nettoyage radars {year}...")
            try:
                radar_cleaners[year]()
                logger.info(f" Nettoyage radars {year} terminé")
            except Exception as e:
                logger.error(f" Erreur nettoyage radars {year}: {e}")
        
        # ============ Charger tout dans la DB ============
        logger.info("Chargement en base de données...")
        load_csv_to_db()
        logger.info("Données prêtes!")
        
    except Exception as e:
        logger.error(f"Erreur setup données: {e}")
        import traceback
        traceback.print_exc()
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
    # Werkzeug sets this to "true" on debug reloads; we only run setup on the FIRST launch
    werkzeug_run = os.environ.get("WERKZEUG_RUN_MAIN")
    logger.info(f"WERKZEUG_RUN_MAIN={werkzeug_run}")
    
    if werkzeug_run != "true":
        setup_data()
    else:
        logger.info("(Debug reload detected; skipping setup_data)")
    
    logger.info("Dashboard sur http://127.0.0.1:8050/")
    # Masquer la barre 'Dash Dev Tools' en bas de page tout en gardant le reload
    app.run(
        debug=True,
        port=8050,
        dev_tools_ui=False,               # cache la barre Errors/Callbacks/Update
        dev_tools_props_check=False,      # évite les popups verbeux
        dev_tools_silence_routes_logging=True,
    )