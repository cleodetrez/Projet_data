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
config_path = Path(__file__).resolve().parents[2] / "config.py"
if config_path.exists():
    import sys
    sys.path.insert(0, str(config_path.parent))
    try:
        from config import (  # type: ignore
            caract_csv_url,
            radar_csv_url,
            caract_csv_url_2021,
            radar_csv_url_2021,
            caract_csv_url_2020,
            caract_csv_url_2022,
            caract_csv_url_2024,
            usager_csv_url_2020,
            usager_csv_url_2021,
            usager_csv_url_2022,
            usager_csv_url_2023,
            usager_csv_url_2024,
            vehicule_csv_url_2020,
            vehicule_csv_url_2021,
            vehicule_csv_url_2022,
            vehicule_csv_url_2023,
            raw_dir,
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "module config introuvable, utilisation des valeurs par défaut."
        )
        caract_csv_url = ""  # type: ignore[assignment]
        radar_csv_url = ""  # type: ignore[assignment]
        caract_csv_url_2021 = ""  # type: ignore[assignment]
        radar_csv_url_2021 = ""  # type: ignore[assignment]
        caract_csv_url_2020 = ""  # type: ignore[assignment]
        caract_csv_url_2022 = ""  # type: ignore[assignment]
        caract_csv_url_2024 = ""  # type: ignore[assignment]
        usager_csv_url_2020 = ""  # type: ignore[assignment]
        usager_csv_url_2021 = ""  # type: ignore[assignment]
        usager_csv_url_2022 = ""  # type: ignore[assignment]
        usager_csv_url_2023 = ""  # type: ignore[assignment]
        usager_csv_url_2024 = ""  # type: ignore[assignment]
        vehicule_csv_url_2020 = ""  # type: ignore[assignment]
        vehicule_csv_url_2021 = ""  # type: ignore[assignment]
        vehicule_csv_url_2022 = ""  # type: ignore[assignment]
        vehicule_csv_url_2023 = ""  # type: ignore[assignment]
        raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"  # type: ignore[assignment]
else:
    caract_csv_url = ""  # type: ignore[assignment]
    radar_csv_url = ""  # type: ignore[assignment]
    caract_csv_url_2021 = ""  # type: ignore[assignment]
    radar_csv_url_2021 = ""  # type: ignore[assignment]
    caract_csv_url_2020 = ""  # type: ignore[assignment]
    caract_csv_url_2022 = ""  # type: ignore[assignment]
    caract_csv_url_2024 = ""  # type: ignore[assignment]
    usager_csv_url_2020 = ""  # type: ignore[assignment]
    usager_csv_url_2021 = ""  # type: ignore[assignment]
    usager_csv_url_2022 = ""  # type: ignore[assignment]
    usager_csv_url_2023 = ""  # type: ignore[assignment]
    usager_csv_url_2024 = ""  # type: ignore[assignment]
    vehicule_csv_url_2020 = ""  # type: ignore[assignment]
    vehicule_csv_url_2021 = ""  # type: ignore[assignment]
    vehicule_csv_url_2022 = ""  # type: ignore[assignment]
    vehicule_csv_url_2023 = ""  # type: ignore[assignment]
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
        logger.info("fichier %s trouve, chargement depuis le cache.", filename)
        return pd.read_csv(file_path, low_memory=False, sep=";")

    if not url:
        raise ValueError(f"url vide pour le fichier demande: {filename}")

    logger.info("telechargement de %s...", filename)
    try:
        resp = requests.get(url, stream=True, timeout=60, headers=HEADERS)
        resp.raise_for_status()

        with file_path.open("wb") as fobj:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fobj.write(chunk)

        logger.info("telechargement de %s termine.", filename)
        return pd.read_csv(file_path, low_memory=False, sep=";")
    except requests.RequestException as err:
        logger.error("erreur lors du telechargement de %s: %s", filename, err)
        raise
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as err:
        logger.error("erreur lecture du fichier %s: %s", filename, err)
        logger.error("le contenu telecharge n'est peut-etre pas un csv valide.")
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
    """charge les caracteristiques 2023 nettoyees."""
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


def get_caract_2021(_force_download: bool = False) -> pd.DataFrame:
    """charge les caractéristiques 2021 nettoyées."""
    cleaned_path = raw_dir.parent / "cleaned" / "caract_clean_2021.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(caract_csv_url_2021, "caracteristiques-2021.csv")
    save_to_db(df, "caracteristiques")
    return df


def get_caract_2020(_force_download: bool = False) -> pd.DataFrame:
    """charge les caractéristiques 2020 nettoyées."""
    cleaned_path = raw_dir.parent / "cleaned" / "caract_clean_2020.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(caract_csv_url_2020, "caracteristiques-2020.csv")
    return df


def get_caract_2022(_force_download: bool = False) -> pd.DataFrame:
    """charge les caractéristiques 2022 nettoyées."""
    cleaned_path = raw_dir.parent / "cleaned" / "caract_clean_2022.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(caract_csv_url_2022, "caracteristiques-2022.csv")
    return df


def get_caract_2024(_force_download: bool = False) -> pd.DataFrame:
    """charge les caractéristiques 2024 nettoyées."""
    cleaned_path = raw_dir.parent / "cleaned" / "caract_clean_2024.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(caract_csv_url_2024, "caracteristiques-2024.csv")
    return df


def get_radar_2021(_force_download: bool = False) -> pd.DataFrame:
    """charge les radars 2021 nettoyés."""
    cleaned_path = raw_dir.parent / "cleaned" / "radars_delta_clean_2021.csv"
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path, low_memory=False)
    else:
        df = dl_csv(radar_csv_url_2021, "radars-2021.csv")
    save_to_db(df, "radars")
    return df

# ------------------------------------------------------------------
# usager (nouveau jeu de données multi-année)
# ------------------------------------------------------------------
def _get_usager_generic(year: int, url: str) -> pd.DataFrame:
    """Télécharge (si besoin) le CSV usagers d'une année et le retourne brut."""
    filename = f"usagers-{year}.csv"
    cleaned_path = raw_dir.parent / "cleaned" / f"usager_clean_{year}.csv"
    raw_path = raw_dir / filename
    if cleaned_path.exists():
        return pd.read_csv(cleaned_path, low_memory=False, sep="," if cleaned_path.suffix == ".csv" else ";")
    if raw_path.exists():
        return pd.read_csv(raw_path, low_memory=False, sep=";")
    return dl_csv(url, filename)

def get_usager_2020() -> pd.DataFrame:
    return _get_usager_generic(2020, usager_csv_url_2020)

def get_usager_2021() -> pd.DataFrame:
    return _get_usager_generic(2021, usager_csv_url_2021)

def get_usager_2022() -> pd.DataFrame:
    return _get_usager_generic(2022, usager_csv_url_2022)

def get_usager_2023() -> pd.DataFrame:
    return _get_usager_generic(2023, usager_csv_url_2023)

def get_usager_2024() -> pd.DataFrame:
    return _get_usager_generic(2024, usager_csv_url_2024)

# ------------------------------------------------------------------
# vehicule (nouveau jeu de données multi-année)
# ------------------------------------------------------------------
def _get_vehicule_generic(year: int, url: str) -> pd.DataFrame:
    """Télécharge (si besoin) le CSV véhicules d'une année et le retourne brut."""
    filename = f"vehicules-{year}.csv"
    cleaned_path = raw_dir.parent / "cleaned" / f"vehicule_clean_{year}.csv"
    raw_path = raw_dir / filename
    if cleaned_path.exists():
        return pd.read_csv(cleaned_path, low_memory=False, sep="," if cleaned_path.suffix == ".csv" else ";")
    if raw_path.exists():
        return pd.read_csv(raw_path, low_memory=False, sep=";")
    return dl_csv(url, filename)

def get_vehicule_2020() -> pd.DataFrame:
    return _get_vehicule_generic(2020, vehicule_csv_url_2020)

def get_vehicule_2021() -> pd.DataFrame:
    return _get_vehicule_generic(2021, vehicule_csv_url_2021)

def get_vehicule_2022() -> pd.DataFrame:
    return _get_vehicule_generic(2022, vehicule_csv_url_2022)

def get_vehicule_2023() -> pd.DataFrame:
    return _get_vehicule_generic(2023, vehicule_csv_url_2023)


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

        # Chargement multi-année des caractéristiques
        caract_loaders = {
            2020: get_caract_2020,
            2021: get_caract_2021,
            2022: get_caract_2022,
            2023: get_caract_2023,
            2024: get_caract_2024,
        }
        for year, fn in caract_loaders.items():
            try:
                df = fn()
                logger.info(
                    "caracteristiques %s : %d lignes, %d colonnes.",
                    year,
                    df.shape[0],
                    df.shape[1],
                )
            except Exception as e:
                logger.warning("echec chargement caracteristiques %s : %s", year, e)

        # Chargement multi-année des radars (années disponibles)
        radar_loaders = {2021: get_radar_2021, 2023: get_radar_2023}
        for year, fn in radar_loaders.items():
            try:
                df = fn()
                logger.info(
                    "radars %s : %d lignes, %d colonnes.",
                    year,
                    df.shape[0],
                    df.shape[1],
                )
            except Exception as e:
                logger.warning("echec chargement radars %s : %s", year, e)

        # Chargement multi-année des usagers
        usager_loaders = {
            2020: get_usager_2020,
            2021: get_usager_2021,
            2022: get_usager_2022,
            2023: get_usager_2023,
            2024: get_usager_2024,
        }
        for year, fn in usager_loaders.items():
            try:
                df = fn()
                logger.info(
                    "usagers %s : %d lignes, %d colonnes.",
                    year,
                    df.shape[0],
                    df.shape[1],
                )
            except Exception as e:
                logger.warning("echec chargement usagers %s : %s", year, e)

        # Chargement multi-année des vehicules
        vehicule_loaders = {
            2020: get_vehicule_2020,
            2021: get_vehicule_2021,
            2022: get_vehicule_2022,
            2023: get_vehicule_2023,
        }
        for year, fn in vehicule_loaders.items():
            try:
                df = fn()
                logger.info(
                    "vehicules %s : %d lignes, %d colonnes.",
                    year,
                    df.shape[0],
                    df.shape[1],
                )
            except Exception as e:
                logger.warning("echec chargement vehicules %s : %s", year, e)

    except Exception as err:  # garder large ici pour un script cli
        logger.error("erreur globale get_data : %s", err)
