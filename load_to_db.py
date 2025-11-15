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
    logger.info(f"Recherche fichiers nettoyes dans {CLEAN_DIR}...")
    for p in CLEAN_DIR.glob("caract_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"caracteristiques_{year}"] = p
        logger.info(f"Trouve: {p.name}")
    
    # Découvrir tous les fichiers radars_delta_clean_YYYY.csv -> radars_YYYY
    for p in CLEAN_DIR.glob("radars_delta_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"radars_{year}"] = p
        logger.info(f"Trouve: {p.name}")

    # Découvrir tous les fichiers usager_clean_YYYY.csv -> usager_YYYY
    for p in CLEAN_DIR.glob("usager_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"usager_{year}"] = p
        logger.info(f"Trouve: {p.name}")

    # Découvrir tous les fichiers vehicule_clean_YYYY.csv -> vehicule_YYYY
    for p in CLEAN_DIR.glob("vehicule_clean_*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if not m:
            continue
        year = m.group(1)
        all_files[f"vehicule_{year}"] = p
        logger.info(f"Trouve: {p.name}")
    
    if not all_files:
        logger.warning(f"Aucun fichier nettoye trouve dans {CLEAN_DIR}")
        return
    
    logger.info(f"{len(all_files)} fichier(s) a charger:")
    for table_name, csv_path in sorted(all_files.items()):
        if not csv_path.exists():
            logger.warning(f"Fichier manquant : {csv_path}")
            continue
        
        attempt = 0
        while attempt < retries:
            try:
                logger.info(f"Chargement de {csv_path.name} table '{table_name}'...")
                df = pd.read_csv(csv_path, low_memory=False)
                
                # Insérer dans la DB (remplace la table)
                df.to_sql(table_name, engine, if_exists="replace", index=False)
                logger.info(f"{len(df)} lignes inserees dans '{table_name}'")
                break
            
            except Exception as e:
                attempt += 1
                if attempt < retries:
                    wait = 2 ** attempt
                    logger.warning(f"Tentative {attempt}/{retries} echouee pour {table_name}, reessai dans {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Erreur definitive pour {csv_path} : {e}")
    
    engine.dispose()
    logger.info(f"Base de données mise à jour : {DATABASE_PATH}")

    # Création des tables jointes caract/usager/vehicule par année
    try:
        engine = create_engine(DATABASE_URL, connect_args={"timeout": 30})
        with engine.connect() as conn:
            # Récupérer les années où les tables existent
            caract_years = [re.search(r"caracteristiques_(\d{4})", t).group(1) for t in all_files.keys() if t.startswith("caracteristiques_")]  # type: ignore
            for year in sorted(caract_years):
                usager_table = f"usager_{year}"
                vehicule_table = f"vehicule_{year}"
                caract_table = f"caracteristiques_{year}"
                
                # Vérifier présence des tables correspondantes
                has_usager = usager_table in all_files
                # Pour 2024, ignorer vehicule même s'il existe
                has_vehicule = vehicule_table in all_files
                
                if not has_usager and not has_vehicule:
                    logger.info(f"Pas de table usager/vehicule pour {year}, jointure ignorée")
                    continue
                
                # Nom de table selon ce qui est joint
                if has_usager and has_vehicule:
                    joined_table = f"caract_usager_vehicule_{year}"
                elif has_usager:
                    joined_table = f"caract_usager_{year}"
                else:
                    joined_table = f"caract_vehicule_{year}"
                
                logger.info(f"Creation table jointe {joined_table} (accidents x usagers x vehicules {year})...")
                
                # Drop si existe
                conn.execute(text(f"DROP TABLE IF EXISTS {joined_table}"))
                
                # Détecter le nom de la colonne d'identifiant dans caracteristiques
                caract_csv = all_files[caract_table]
                df_caract_sample = pd.read_csv(caract_csv, nrows=0)
                
                # Chercher la colonne d'identifiant (acc_id, Num_Acc, ou Accident_Id)
                id_col = None
                for possible_id in ["acc_id", "Num_Acc", "Accident_Id"]:
                    if possible_id in df_caract_sample.columns:
                        id_col = possible_id
                        break
                
                if not id_col:
                    logger.error(f"Aucune colonne d'identifiant trouvée dans {caract_table}")
                    continue
                
                logger.info(f"Utilisation de la colonne '{id_col}' pour les jointures")
                
                # Création via LEFT JOINs pour ne pas perdre d'accidents
                # Vérifier les colonnes disponibles dans vehicule pour cette année
                vehicule_cols = []
                if has_vehicule:
                    # Lire les colonnes du CSV vehicule pour cette année
                    vehicule_csv = all_files[vehicule_table]
                    df_vehicule_sample = pd.read_csv(vehicule_csv, nrows=0)
                    vehicule_cols = [c for c in ["catv", "motor"] if c in df_vehicule_sample.columns]
                
                # Construire le SELECT dynamiquement selon les colonnes disponibles
                if has_usager and has_vehicule:
                    vehicule_select = ", ".join([f"v.{col}" for col in vehicule_cols]) if vehicule_cols else ""
                    select_clause = f"c.*, u.sexe, u.an_nais, u.trajet, u.grav{', ' + vehicule_select if vehicule_select else ''}"
                    join_sql = f"""
                    CREATE TABLE {joined_table} AS
                    SELECT {select_clause}
                    FROM {caract_table} c
                    LEFT JOIN {usager_table} u ON c.{id_col} = u.Num_Acc
                    LEFT JOIN {vehicule_table} v ON c.{id_col} = v.Num_Acc
                    """
                elif has_usager:
                    join_sql = f"""
                    CREATE TABLE {joined_table} AS
                    SELECT c.*, u.sexe, u.an_nais, u.trajet, u.grav
                    FROM {caract_table} c
                    LEFT JOIN {usager_table} u ON c.{id_col} = u.Num_Acc
                    """
                else:  # has_vehicule only
                    vehicule_select = ", ".join([f"v.{col}" for col in vehicule_cols])
                    join_sql = f"""
                    CREATE TABLE {joined_table} AS
                    SELECT c.*, {vehicule_select}
                    FROM {caract_table} c
                    LEFT JOIN {vehicule_table} v ON c.{id_col} = v.Num_Acc
                    """
                
                conn.execute(text(join_sql))
                logger.info(f"Table {joined_table} creee")
            conn.commit()
        engine.dispose()
    except Exception as e:
        logger.error(f"Erreur creation des tables jointes: {e}")
if __name__ == "__main__":
    load_csv_to_db()
