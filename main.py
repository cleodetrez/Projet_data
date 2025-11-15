"""point d'entrée dash : setup + lancement complet."""

import sys
import logging
from pathlib import Path
import re

import pandas as pd

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
    """Telecharge, nettoie et charge tout dans la DB."""
    logger.info(" Initialisation des donnees...")
    
    try:
        # Imports locaux - Caractéristiques
        from src.utils.get_data import (
            get_caract_2020, get_caract_2021, get_caract_2022, 
            get_caract_2023, get_caract_2024,
            get_radar_2021, get_radar_2023,
            get_usager_2020, get_usager_2021, get_usager_2022,
            get_usager_2023, get_usager_2024,
            get_vehicule_2020, get_vehicule_2021, get_vehicule_2022, get_vehicule_2023
        )
        from src.utils.clean_caract_2020 import clean_caracteristiques as clean_caract_2020
        from src.utils.clean_caract_2021 import clean_caracteristiques as clean_caract_2021
        from src.utils.clean_caract_2022 import clean_caracteristiques as clean_caract_2022
        from src.utils.clean_caract_2023 import clean_caracteristiques as clean_caract_2023
        from src.utils.clean_caract_2024 import clean_caracteristiques as clean_caract_2024
        
        # Imports locaux - Radars
        from src.utils.clean_radars_2021 import clean_radars as clean_radars_2021
        from src.utils.clean_radars_2023 import clean_radars as clean_radars_2023
        
        # Imports locaux - Usagers
        from src.utils.clean_usager_2020 import clean_usager_2020
        from src.utils.clean_usager_2021 import clean_usager_2021
        from src.utils.clean_usager_2022 import clean_usager_2022
        from src.utils.clean_usager_2023 import clean_usager_2023
        from src.utils.clean_usager_2024 import clean_usager_2024
        
        # Imports locaux - Vehicules
        from src.utils.clean_vehicule_2020 import clean_vehicule_2020
        from src.utils.clean_vehicule_2021 import clean_vehicule_2021
        from src.utils.clean_vehicule_2022 import clean_vehicule_2022
        from src.utils.clean_vehicule_2023 import clean_vehicule_2023
        
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
        
        usager_cleaners = {
            2020: clean_usager_2020,
            2021: clean_usager_2021,
            2022: clean_usager_2022,
            2023: clean_usager_2023,
            2024: clean_usager_2024,
        }
        
        usager_getters = {
            2020: get_usager_2020,
            2021: get_usager_2021,
            2022: get_usager_2022,
            2023: get_usager_2023,
            2024: get_usager_2024,
        }
        
        vehicule_cleaners = {
            2020: clean_vehicule_2020,
            2021: clean_vehicule_2021,
            2022: clean_vehicule_2022,
            2023: clean_vehicule_2023,
        }
        
        vehicule_getters = {
            2020: get_vehicule_2020,
            2021: get_vehicule_2021,
            2022: get_vehicule_2022,
            2023: get_vehicule_2023,
        }
        
        # ============ Nettoyer CARACTÉRISTIQUES (5 années) ============
        logger.info("Traitement CARACTERISTIQUES...")
        for year in caract_cleaners.keys():
            cleaned_path = ROOT / "data" / "cleaned" / f"caract_clean_{year}.csv"
            raw_path = ROOT / "data" / "raw" / f"caracteristiques-{year}.csv"
            
            # Vérifier si le fichier nettoyé a la bonne structure (avec acc_id)
            needs_recleaning = False
            if cleaned_path.exists():
                try:
                    df_check = pd.read_csv(cleaned_path, nrows=0)
                    if "acc_id" not in df_check.columns and ("Num_Acc" in df_check.columns or "Accident_Id" in df_check.columns):
                        logger.warning(f"caract_clean_{year}.csv utilise l'ancien format (sans acc_id), re-nettoyage...")
                        needs_recleaning = True
                        cleaned_path.unlink()  # Supprimer l'ancien fichier
                except Exception as e:
                    logger.warning(f"Erreur lecture {cleaned_path.name}: {e}, re-nettoyage...")
                    needs_recleaning = True
                    if cleaned_path.exists():
                        cleaned_path.unlink()
            
            if cleaned_path.exists() and not needs_recleaning:
                logger.info(f"caract_clean_{year}.csv existe deja")
                continue
            
            if not raw_path.exists():
                logger.info(f"Telechargement caracteristiques-{year}.csv...")
                try:
                    caract_getters[year]()
                    logger.info(f"Telechargement {year} termine")
                except Exception as e:
                    logger.error(f" Erreur telechargement caract {year}: {e}")
                    continue
            
            logger.info(f" Nettoyage caract {year}...")
            try:
                caract_cleaners[year]()
                logger.info(f"Nettoyage caract {year} termine")
            except Exception as e:
                logger.error(f" Erreur nettoyage caract {year}: {e}")
        
        # ============ Nettoyer RADARS (2 années) ============
        logger.info("Traitement RADARS...")
        for year in radar_cleaners.keys():
            cleaned_path = ROOT / "data" / "cleaned" / f"radars_delta_clean_{year}.csv"
            raw_path = ROOT / "data" / "raw" / f"radars-{year}.csv"
            
            if cleaned_path.exists():
                logger.info(f"radars_delta_clean_{year}.csv existe deja")
                continue
            
            if not raw_path.exists():
                logger.info(f"Telechargement radars-{year}.csv...")
                try:
                    radar_getters[year]()
                    logger.info(f"Telechargement radars {year} termine")
                except Exception as e:
                    logger.error(f" Erreur telechargement radars {year}: {e}")
                    continue
            
            logger.info(f" Nettoyage radars {year}...")
            try:
                radar_cleaners[year]()
                logger.info(f" Nettoyage radars {year} terminé")
            except Exception as e:
                logger.error(f" Erreur nettoyage radars {year}: {e}")
        
        # ============ Nettoyer USAGERS (5 années) ============
        logger.info("Traitement USAGERS...")
        for year in usager_cleaners.keys():
            cleaned_path = ROOT / "data" / "cleaned" / f"usager_clean_{year}.csv"
            raw_path = ROOT / "data" / "raw" / f"usagers-{year}.csv"
            
            if cleaned_path.exists():
                logger.info(f"usager_clean_{year}.csv existe deja")
                continue
            
            if not raw_path.exists():
                logger.info(f"Telechargement usagers-{year}.csv...")
                try:
                    usager_getters[year]()
                    logger.info(f"Telechargement usagers {year} termine")
                except Exception as e:
                    logger.error(f" Erreur telechargement usagers {year}: {e}")
                    continue
            
            logger.info(f" Nettoyage usagers {year}...")
            try:
                usager_cleaners[year]()
                logger.info(f"Nettoyage usagers {year} termine")
            except Exception as e:
                logger.error(f" Erreur nettoyage usagers {year}: {e}")
        
        # ============ Nettoyer VEHICULES (4 années) ============
        logger.info("Traitement VEHICULES...")
        for year in vehicule_cleaners.keys():
            cleaned_path = ROOT / "data" / "cleaned" / f"vehicule_clean_{year}.csv"
            raw_path = ROOT / "data" / "raw" / f"vehicules-{year}.csv"
            
            if cleaned_path.exists():
                logger.info(f"vehicule_clean_{year}.csv existe deja")
                continue
            
            if not raw_path.exists():
                logger.info(f"Telechargement vehicules-{year}.csv...")
                try:
                    vehicule_getters[year]()
                    logger.info(f"Telechargement vehicules {year} termine")
                except Exception as e:
                    logger.error(f" Erreur telechargement vehicules {year}: {e}")
                    continue
            
            logger.info(f" Nettoyage vehicules {year}...")
            try:
                vehicule_cleaners[year]()
                logger.info(f"Nettoyage vehicules {year} termine")
            except Exception as e:
                logger.error(f" Erreur nettoyage vehicules {year}: {e}")
        
        # ============ Charger tout dans la DB ============
        # TOUJOURS charger la DB (même si les CSV existent déjà)
        # car les tables jointes doivent être créées
        logger.info("Chargement en base de donnees...")
        try:
            load_csv_to_db()
            logger.info("Donnees pretes!")
        except Exception as e:
            logger.error(f"Erreur chargement DB: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        logger.error(f"Erreur setup donnees: {e}")
        import traceback
        traceback.print_exc()
        logger.warning("Tentative de lancement du dashboard malgre l'erreur...")
        # Ne pas exit - laisser le dashboard se lancer quand même


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
    from pathlib import Path
    from sqlalchemy import create_engine, inspect
    
    # Werkzeug sets this to "true" on debug reloads; we only run setup on the FIRST launch
    werkzeug_run = os.environ.get("WERKZEUG_RUN_MAIN")
    logger.info(f"WERKZEUG_RUN_MAIN={werkzeug_run}")
    
    # Flag pour éviter la boucle infinie de rechargement
    setup_done_flag = ROOT / "bdd" / ".setup_done"
    
    # Vérifier si les tables jointes existent
    db_path = ROOT / "bdd" / "database.db"
    need_setup = False
    
    if not db_path.exists():
        logger.info("Base de données inexistante, setup requis")
        need_setup = True
    else:
        try:
            engine = create_engine(f"sqlite:///{db_path.as_posix()}")
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Vérifier si les tables jointes essentielles existent
            required_tables = [
                "caract_usager_vehicule_2020",
                "caract_usager_vehicule_2021",
                "caract_usager_vehicule_2022", 
                "caract_usager_vehicule_2023"
            ]
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                logger.warning(f"Tables manquantes: {missing_tables}")
                # Ne recharger que si ce n'est pas un reload de debug OU si le flag n'existe pas
                if werkzeug_run != "true" or not setup_done_flag.exists():
                    logger.info("Rechargement de la base nécessaire")
                    need_setup = True
                else:
                    logger.error(f"Tables toujours manquantes après setup: {missing_tables}")
                    logger.error("Vérifiez les erreurs dans les logs ci-dessus")
                    logger.info("Lancement du dashboard malgré les tables manquantes...")
            else:
                logger.info("Toutes les tables jointes présentes")
                # Créer le flag si toutes les tables sont présentes
                if not setup_done_flag.exists():
                    setup_done_flag.touch()
            
            engine.dispose()
        except Exception as e:
            logger.error(f"Erreur vérification DB: {e}")
            if werkzeug_run != "true":
                need_setup = True
    
    if werkzeug_run != "true":
        # Supprimer le flag au premier lancement
        if setup_done_flag.exists():
            setup_done_flag.unlink()
        setup_data()
        # Créer le flag après setup réussi
        setup_done_flag.touch()
    elif need_setup:
        logger.info("Tables manquantes détectées, rechargement forcé (une seule fois)...")
        setup_data()
        # Créer le flag pour éviter la boucle
        setup_done_flag.touch()
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