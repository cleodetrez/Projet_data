"""
load_to_db.py : Charge les fichiers CSV nettoyés dans la base SQLite
"""
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
CLEAN_DIR = ROOT / "data" / "cleaned"
DB_DIR = ROOT / "bdd"
DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DB_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

def load_csv_to_db():
    """Charge dynamiquement les fichiers CSV nettoyés (toutes années) dans SQLite."""
    
    engine = create_engine(DATABASE_URL)
    
    all_files: dict[str, Path] = {}
    
    # Découvrir tous les fichiers caract_clean_YYYY.csv -> caracteristiques_YYYY
    for p in CLEAN_DIR.glob("caract_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"caracteristiques_{year}"] = p
    
    # Découvrir tous les fichiers radars_delta_clean_YYYY.csv -> radars_YYYY
    for p in CLEAN_DIR.glob("radars_delta_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"radars_{year}"] = p
    
    if not all_files:
        logger.warning(f"Aucun fichier nettoyé trouvé dans {CLEAN_DIR}")
        return
    
    for table_name, csv_path in sorted(all_files.items()):
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
