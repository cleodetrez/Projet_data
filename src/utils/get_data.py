from config import caract_csv_url, radar_csv_url, raw_dir
from pathlib import Path
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

def get_caract_2023(force_download=False):
    return dl_csv(caract_csv_url, "caracteristiques-2023.csv")

def get_radar_2023(force_download=False):
    return dl_csv(radar_csv_url, "radars-2023.csv")

if __name__ == "__main__":
    try:
        df_caract = get_caract_2023()
        logger.info(f"donnees caracteristiques 2023 chargees : {df_caract.shape[0]} lignes, {df_caract.shape[1]} colonnes.")
    except Exception as e:
        logger.error(f"echec du chargement des donnees caracteristiques 2023: {e}")

    try:
        df_radar = get_radar_2023()
        logger.info(f"donnees radars 2023 chargees : {df_radar.shape[0]} lignes, {df_radar.shape[1]} colonnes.")
    except Exception as e:
        logger.error(f"echec du chargement des donnees radars 2023: {e}")