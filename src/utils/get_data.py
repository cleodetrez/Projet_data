from config import url1, url2, RAW_DIR
from pathlib import Path
import requests
import zipfile
import io
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = Path(RAW_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _download_and_extract_csvs(url, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Téléchargement : %s", url)
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    filename = url.split("/")[-1].split("?")[0] or "resource"
    content = r.content
    content_type = r.headers.get("content-type", "").lower()
    out_paths = []

    if "zip" in content_type or filename.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            for member in z.namelist():
                # on prend uniquement le nom de fichier pour éviter path traversal
                name = Path(member).name
                if name.lower().endswith(".csv"):
                    target = dest_dir / name
                    with target.open("wb") as f:
                        f.write(z.read(member))
                    out_paths.append(target)
        # si aucun CSV extrait, sauvegarder le zip
        if not out_paths:
            target = dest_dir / filename
            with target.open("wb") as f:
                f.write(content)
            out_paths.append(target)
        return out_paths

    # fichier direct (souvent CSV)
    target = dest_dir / filename
    with target.open("wb") as f:
        f.write(content)
    return [target]


def _load_csvs(paths):
    dfs = []
    for p in paths:
        try:
            dfs.append(pd.read_csv(p, low_memory=False))
        except Exception as e:
            logger.warning("Impossible de lire %s : %s", p, e)
    if not dfs:
        raise RuntimeError("Aucun CSV valide n'a été chargé.")
    return pd.concat(dfs, ignore_index=True, sort=False)


def get_dataset_from_source(src, name, force_download=False):
    target_dir = CACHE_DIR / name
    target_dir.mkdir(parents=True, exist_ok=True)

    cached_csvs = list(target_dir.glob("*.csv"))
    if cached_csvs and not force_download:
        logger.info("Chargement depuis le cache %s (%d fichiers)", target_dir, len(cached_csvs))
        return _load_csvs(cached_csvs)

    # on considère src comme l'URL que tu fournis (pas de traitement supplémentaire)
    urls = [str(src).strip()]

    all_csv_paths = []
    for u in urls:
        try:
            paths = _download_and_extract_csvs(u, target_dir)
            all_csv_paths.extend([p for p in paths if p.suffix.lower() == ".csv"])
        except Exception as e:
            logger.warning("Erreur téléchargement %s : %s", u, e)

    if not all_csv_paths:
        raise RuntimeError(f"Aucun CSV trouvé pour la source : {src}")

    return _load_csvs(all_csv_paths)


def get_data1(force_download=False):
    return get_dataset_from_source(url1, "data1", force_download=force_download)


def get_data2(force_download=False):
    return get_dataset_from_source(url2, "data2", force_download=force_download)


if __name__ == "__main__":
    try:
        df1 = get_data1()
        logger.info("data1: %d lignes, %d colonnes", df1.shape[0], df1.shape[1])
    except Exception as e:
        logger.error("Échec data1: %s", e)

    try:
        df2 = get_data2()
        logger.info("data2: %d lignes, %d colonnes", df2.shape[0], df2.shape[1])
    except Exception as e:
        logger.error("Échec data2: %s", e)
