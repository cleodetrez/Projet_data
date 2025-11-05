import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import caract_csv_url, radar_csv_url, raw_dir
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import requests
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

raw_dir.mkdir(parents=True, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

DATABASE_URL = "sqlite:///bdd/database.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def dl_csv(url, nom_fichier):
    chemin_fichier = raw_dir / nom_fichier
    if chemin_fichier.exists():
        logger.info(f"fichier {nom_fichier} trouve, chargement depuis le cache.")
        return pd.read_csv(chemin_fichier, low_memory=False, sep=';')

    logger.info(f"telechargement de {nom_fichier}...")
    try:
        r = requests.get(url, stream=True, timeout=60, headers=headers)
        r.raise_for_status()
        
        with chemin_fichier.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"telechargement de {nom_fichier} termine.")
        return pd.read_csv(chemin_fichier, low_memory=False, sep=';')

    except requests.RequestException as e:
        logger.error(f"erreur lors du telechargement de {nom_fichier}: {e}")
        raise
    except Exception as e:
        logger.error(f"erreur lors de la lecture du fichier {nom_fichier}: {e}")
        logger.error("le contenu telecharge n'est peut-etre pas un csv valide.")
        raise

def init_db():
    # Créer les tables
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS caracteristiques (
            Num_Acc TEXT PRIMARY KEY,
            lat FLOAT,
            long FLOAT,
            date TEXT,
            departement TEXT
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS radars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat FLOAT,
            long FLOAT,
            departement TEXT,
            type TEXT
        )
        """))
        conn.commit()

def save_to_db(df, table_name):
    """Sauvegarde un DataFrame dans la base de données"""
    df.to_sql(table_name, engine, if_exists='replace', index=False)

def get_caract_2023(force_download=False):
    df = dl_csv(caract_csv_url, "caracteristiques-2023.csv")
    save_to_db(df, 'caracteristiques')
    return df

def get_radar_2023(force_download=False):
    df = dl_csv(radar_csv_url, "radars-2023.csv")
    save_to_db(df, 'radars')
    return df

def query_db(query, params=None):
    """Exécute une requête SQL"""
    with Session() as session:
        result = session.execute(text(query), params or {})
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# Exemple de fonction utilisant une requête SQL
def get_accidents_by_department(department):
    query = """
    SELECT * FROM caracteristiques 
    WHERE departement = :dept
    """
    return query_db(query, {"dept": department})

if __name__ == "__main__":
    try:
        # Initialiser la base de données
        init_db()
        
        # Charger les données
        df_caract = get_caract_2023()
        logger.info(f"donnees caracteristiques 2023 chargees : {df_caract.shape[0]} lignes, {df_caract.shape[1]} colonnes.")
        
        df_radar = get_radar_2023()
        logger.info(f"donnees radars 2023 chargees : {df_radar.shape[0]} lignes, {df_radar.shape[1]} colonnes.")
        
        # Exemple d'utilisation d'une requête
        result = get_accidents_by_department("75")
        logger.info(f"Nombre d'accidents à Paris : {len(result)}")
        
    except Exception as e:
        logger.error(f"Erreur : {e}")