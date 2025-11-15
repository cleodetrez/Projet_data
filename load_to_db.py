"""
load_to_db.py : Charge les fichiers CSV nettoyés dans la base SQLite
"""
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
import logging
import re
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
CLEAN_DIR = ROOT / "data" / "cleaned"
DB_DIR = ROOT / "bdd"
DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DB_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}?timeout=30"

def load_csv_to_db(retries=3):
    """Charge dynamiquement les fichiers CSV nettoyés (toutes années) dans SQLite."""
    
    engine = create_engine(DATABASE_URL, connect_args={"timeout": 30})
    
    all_files: dict[str, Path] = {}
    
    # Découvrir tous les fichiers caract_clean_YYYY.csv -> caracteristiques_YYYY
    logger.info(f"Recherche fichiers nettoyés dans {CLEAN_DIR}...")
    for p in CLEAN_DIR.glob("caract_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"caracteristiques_{year}"] = p
        logger.info(f"  → Trouvé: {p.name}")
    
    # Découvrir tous les fichiers radars_delta_clean_YYYY.csv -> radars_YYYY
    for p in CLEAN_DIR.glob("radars_delta_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"radars_{year}"] = p
        logger.info(f"  → Trouvé: {p.name}")

    # Découvrir tous les fichiers usager_clean_YYYY.csv -> usager_YYYY
    for p in CLEAN_DIR.glob("usager_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"usager_{year}"] = p
        logger.info(f"  → Trouvé: {p.name}")
    
    if not all_files:
        logger.warning(f"Aucun fichier nettoyé trouvé dans {CLEAN_DIR}")
        return
    
    logger.info(f"{len(all_files)} fichier(s) à charger:")
    for table_name, csv_path in sorted(all_files.items()):
        if not csv_path.exists():
            logger.warning(f"Fichier manquant : {csv_path}")
            continue
        
        attempt = 0
        while attempt < retries:
            try:
                logger.info(f"Chargement de {csv_path.name} → table '{table_name}'...")
                df = pd.read_csv(csv_path, low_memory=False)
                
                # Insérer dans la DB (remplace la table)
                df.to_sql(table_name, engine, if_exists="replace", index=False)
                logger.info(f"✓ {len(df)} lignes insérées dans '{table_name}'")
                break
            
            except Exception as e:
                attempt += 1
                if attempt < retries:
                    wait = 2 ** attempt
                    logger.warning(f"Tentative {attempt}/{retries} échouée pour {table_name}, réessai dans {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Erreur définitive pour {csv_path} : {e}")
    
    engine.dispose()
    logger.info(f"Base de données mise à jour : {DATABASE_PATH}")

    # Création des tables jointes caract/usager par année
    try:
        engine = create_engine(DATABASE_URL, connect_args={"timeout": 30})
        with engine.connect() as conn:
            # Récupérer les années où les deux tables existent
            caract_years = [re.search(r"caracteristiques_(\d{4})", t).group(1) for t in all_files.keys() if t.startswith("caracteristiques_")]  # type: ignore
            for year in sorted(caract_years):
                usager_table = f"usager_{year}"
                caract_table = f"caracteristiques_{year}"
                # Vérifier présence du fichier usager correspondant
                if usager_table not in all_files:
                    logger.info(f"Pas de table usager pour {year}, jointure ignorée")
                    continue
                joined_table = f"caract_usager_{year}"
                logger.info(f"Création table jointe {joined_table} (accidents x usagers {year})...")
                # Drop si existe
                conn.execute(text(f"DROP TABLE IF EXISTS {joined_table}"))
                # Création via LEFT JOIN pour ne pas perdre d'accidents
                join_sql = f"""
                CREATE TABLE {joined_table} AS
                SELECT c.*, u.sexe, u.an_nais, u.trajet
                FROM {caract_table} c
                LEFT JOIN {usager_table} u ON c.acc_id = u.Num_Acc
                """
                conn.execute(text(join_sql))
                logger.info(f"✓ Table {joined_table} créée")
            conn.commit()
        engine.dispose()
    except Exception as e:
        logger.error(f"Erreur création des tables jointes: {e}")

if __name__ == "__main__":
    load_csv_to_db()
