"""
load_to_db.py : Charge les fichiers CSV nettoyés dans la base SQLite
"""
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
CLEAN_DIR = ROOT / "data" / "cleaned"
DB_DIR = ROOT / "bdd"
DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DB_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

def load_csv_to_db():
    """Charge les fichiers CSV nettoyés dans la base SQLite."""
    
    engine = create_engine(DATABASE_URL)
    
    # Fichiers à charger pour 2023
    files_2023 = {
        "caracteristiques_2023": CLEAN_DIR / "caract_clean_2023.csv",
        "radars_2023": CLEAN_DIR / "radars_delta_clean_2023.csv",
    }
    
    # Fichiers à charger pour 2021
    files_2021 = {
        "caracteristiques_2021": CLEAN_DIR / "caract_clean_2021.csv",
        "radars_2021": CLEAN_DIR / "radars_delta_clean_2021.csv",
    }
    
    all_files = {**files_2023, **files_2021}
    
    for table_name, csv_path in all_files.items():
        if not csv_path.exists():
            logger.warning(f"Fichier manquant : {csv_path}")
            continue
        
        try:
            logger.info(f"Chargement de {csv_path.name} → table '{table_name}'...")
            df = pd.read_csv(csv_path, low_memory=False)
            
            # Insérer dans la DB (remplace la table)
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            logger.info(f"✓ {len(df)} lignes insérées dans '{table_name}'")
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {csv_path} : {e}")
    
    logger.info(f"✓ Base de données mise à jour : {DATABASE_PATH}")

if __name__ == "__main__":
    load_csv_to_db()
