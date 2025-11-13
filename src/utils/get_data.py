"""outils d'accès données : téléchargement csv, initialisation sqlite, requêtes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------
# configuration (tolère l'absence de `config.py`)
# ---------------------------------------------------------------------
try:
    from config import caract_csv_url, radar_csv_url, raw_dir  # type: ignore
except ImportError:
    logging.getLogger(__name__).warning(
        "module config introuvable, utilisation des valeurs par défaut."
    )
    caract_csv_url = ""  # type: ignore[assignment]
    radar_csv_url = ""  # type: ignore[assignment]
    raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"  # type: ignore[assignment]

# ---------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# constantes et objets globaux
# ---------------------------------------------------------------------
raw_dir.mkdir(parents=True, exist_ok=True)

HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

DATABASE_URL = "sqlite:///bdd/database.db"
ENGINE = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=ENGINE)


# ---------------------------------------------------------------------
# fonctions
# ---------------------------------------------------------------------
def dl_csv(url: str, filename: str) -> pd.DataFrame:
    """télécharge (avec cache) un csv puis le charge en dataframe."""
    file_path = Path(raw_dir) / filename
    if file_path.exists():
        logger.info("fichier %s trouvé, chargement depuis le cache.", filename)
        return pd.read_csv(file_path, low_memory=False, sep=";")

    if not url:
        raise ValueError(f"url vide pour le fichier demandé: {filename}")

    logger.info("téléchargement de %s...", filename)
    try:
        resp = requests.get(url, stream=True, timeout=60, headers=HEADERS)
        resp.raise_for_status()

        with file_path.open("wb") as fobj:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fobj.write(chunk)

        logger.info("téléchargement de %s terminé.", filename)
        return pd.read_csv(file_path, low_memory=False, sep=";")
    except requests.RequestException as err:
        logger.error("erreur lors du téléchargement de %s: %s", filename, err)
        raise
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as err:
        logger.error("erreur lecture du fichier %s: %s", filename, err)
        logger.error("le contenu téléchargé n'est peut-être pas un csv valide.")
        raise


def init_db() -> None:
    """crée les tables si nécessaire."""
    with ENGINE.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS caracteristiques (
                    Num_Acc TEXT PRIMARY KEY,
                    lat FLOAT,
                    long FLOAT,
                    date TEXT,
                    departement TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS radars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat FLOAT,
                    long FLOAT,
                    departement TEXT,
                    type TEXT
                )
                """
            )
        )
        conn.commit()


def save_to_db(df: pd.DataFrame, table_name: str) -> None:
    """sauvegarde un dataframe dans la base sqlite."""
    df.to_sql(table_name, ENGINE, if_exists="replace", index=False)


def get_caract_2023(_force_download: bool = False) -> pd.DataFrame:
    """charge les caractéristiques 2023 nettoyées."""
    # Charger le fichier nettoyé si disponible, sinon le fichier brut
    cleaned_path = raw_dir.parent / "cleaned" / "caract_clean_2023.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(caract_csv_url, "caracteristiques-2023.csv")
    save_to_db(df, "caracteristiques")
    return df


def get_radar_2023(_force_download: bool = False) -> pd.DataFrame:
    """charge les radars 2023 nettoyés."""
    # Charger le fichier nettoyé si disponible, sinon le fichier brut
    cleaned_path = raw_dir.parent / "cleaned" / "radars_delta_clean_2023.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(radar_csv_url, "radars-2023.csv")
    save_to_db(df, "radars")
    return df


def query_db(query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """exécute une requête sql et retourne un dataframe."""
    with SessionLocal() as session:
        res = session.execute(text(query), params or {})
        return pd.DataFrame(res.fetchall(), columns=res.keys())


def get_accidents_by_department(department: str) -> pd.DataFrame:
    """exemple d'accès : accidents pour un département."""
    sql = """
        SELECT * FROM caracteristiques
        WHERE dep = :dept
    """
    return query_db(sql, {"dept": department})


if __name__ == "__main__":
    try:
        init_db()

        df_caract = get_caract_2023()
        logger.info(
            "données caractéristiques 2023 chargées : %d lignes, %d colonnes.",
            df_caract.shape[0],
            df_caract.shape[1],
        )

        df_radar = get_radar_2023()
        logger.info(
            "données radars 2023 chargées : %d lignes, %d colonnes.",
            df_radar.shape[0],
            df_radar.shape[1],
        )

        paris = get_accidents_by_department("75")
        logger.info("nombre d'accidents à paris : %d", len(paris))
    except Exception as err:  # garder large ici pour un script cli
        logger.error("erreur : %s", err)
