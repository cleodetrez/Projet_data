import pandas as pd
from pathlib import Path
import logging
from typing import Union, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_cleaned_year(year: Union[str, int],
                       cleaned_dir: Union[str, Path] = None,
                       output_file: Optional[Union[str, Path]] = None,
                       pattern: Optional[str] = None,
                       primary_key: Optional[str] = None) -> Path:
    """
    Regroupe tous les CSV nettoyés d'une même année en un seul CSV.
    - year: '2023' ou 2023 (si None, regroupe tous les CSV du dossier)
    - cleaned_dir: dossier contenant les fichiers nettoyés (par défaut data/cleaned à la racine du projet)
    - output_file: chemin de sortie (si None -> cleaned_{year}.csv ou cleaned_all.csv)
    - pattern: glob pattern optionnel (par défaut '*{year}*.csv' ou '*.csv' si year est None)
    - primary_key: colonne pour dédoublonner (ex: 'Num_Acc' ou 'accident_id')
    Retourne le Path du fichier de sortie.
    """
    # par défaut, prendre data/cleaned à la racine du projet
    if cleaned_dir is None:
        cleaned_dir = Path(__file__).parents[2] / 'data' / 'cleaned'
    cleaned_dir = Path(cleaned_dir).expanduser().resolve()

    if year is None:
        default_pattern = '*.csv'
    else:
        default_pattern = pattern if pattern is not None else f'*{year}*.csv'

    files = sorted(cleaned_dir.glob(default_pattern))

    # fallback : si aucun fichier avec l'année trouvé, prendre tous les CSV et logger
    if not files:
        fallback = sorted(cleaned_dir.glob('*.csv'))
        if fallback:
            logger.warning(f"Aucun fichier trouvé avec le pattern {default_pattern}. Utilisation de tous les CSV ({len(fallback)} fichiers) dans {cleaned_dir}.")
            files = fallback
        else:
            raise FileNotFoundError(f"Aucun fichier CSV trouvé dans {cleaned_dir} (pattern recherché: {default_pattern})")

    dfs = []
    for f in files:
        try:
            # lecture prioritaire avec séparateur ';' (souvent le cas)
            df = pd.read_csv(f, low_memory=False, sep=';')
        except Exception:
            # fallback lecture automatique
            df = pd.read_csv(f, low_memory=False)
        dfs.append(df)
        logger.info(f"lu {f.name} -> {len(df)} lignes, {len(df.columns)} colonnes")

    combined = pd.concat(dfs, ignore_index=True, sort=False)

    if primary_key and primary_key in combined.columns:
        before = len(combined)
        combined = combined.drop_duplicates(subset=[primary_key])
        logger.info(f"suppression de {before - len(combined)} doublons sur la clé {primary_key}")
    else:
        before = len(combined)
        combined = combined.drop_duplicates()
        logger.info(f"suppression de {before - len(combined)} doublons (général)")

    if output_file is None:
        name = f'cleaned_{year}' if year is not None else 'cleaned_all'
        output_file = cleaned_dir / f'{name}.csv'
    output_file = Path(output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_file, index=False)
    logger.info(f"fichier combiné sauvegardé : {output_file} ({len(combined)} lignes)")

    return output_file

if __name__ == "__main__":
    # exemple d'utilisation depuis la racine du projet
    out = merge_cleaned_year(2023, cleaned_dir=Path(__file__).parents[2] / 'data' / 'cleaned', primary_key='Num_Acc')
    print(f"Saved combined file: {out}")