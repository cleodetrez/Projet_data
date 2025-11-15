"""fusionne les csv nettoyés d'une année en un seul fichier."""

from __future__ import annotations

from pathlib import Path
import logging
from typing import Optional, Union

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_cleaned_year(
    year: Union[str, int, None],
    cleaned_dir: Union[str, Path, None] = None,
    output_file: Optional[Union[str, Path]] = None,
    pattern: Optional[str] = None,
    primary_key: Optional[str] = None,
) -> Path:
    """regroupe tous les csv nettoyés d'une même année en un seul csv.

    args:
        year: '2023' ou 2023. si None, regroupe tous les csv du dossier.
        cleaned_dir: dossier des fichiers nettoyés
            (défaut: data/cleaned à la racine du projet).
        output_file: chemin de sortie. si None -> cleaned_{year}.csv
            ou cleaned_all.csv.
        pattern: motif glob optionnel. par défaut '*{year}*.csv' (ou '*.csv').
        primary_key: colonne utilisée pour dédoublonner
            (ex: 'Num_Acc' ou 'accident_id').

    returns:
        Path: chemin du fichier csv combiné.
    """
    # répertoire par défaut: <racine>/data/cleaned
    if cleaned_dir is None:
        cleaned_dir = Path(__file__).parents[2] / "data" / "cleaned"
    cleaned_dir = Path(cleaned_dir).expanduser().resolve()

    if year is None:
        default_pattern = "*.csv"
    else:
        # pattern spécifique: uniquement les fichiers "caract_clean_YEAR.csv"
        default_pattern = pattern if pattern is not None else f"caract_clean_{year}.csv"

    files = sorted(cleaned_dir.glob(default_pattern))

    # fallback : si aucun fichier ne correspond, prendre tous les csv et logguer
    if not files:
        fallback = sorted(cleaned_dir.glob("*.csv"))
        if fallback:
            logger.warning(
                "aucun fichier pour le pattern %s. utilisation de tous les csv "
                "(%d fichiers) dans %s.",
                default_pattern,
                len(fallback),
                cleaned_dir,
            )
            files = fallback
        else:
            raise FileNotFoundError(
                f"aucun fichier csv trouvé dans {cleaned_dir} "
                f"(pattern recherché: {default_pattern})"
            )

    dfs = []
    for fpath in files:
        # ignorer les fichiers radars (trop volumineux)
        if "radar" in fpath.name.lower():
            logger.info("ignoré (fichier radars): %s", fpath.name)
            continue

        try:
            # essayer d'abord sans spécifier le séparateur (détection auto)
            df = pd.read_csv(fpath, low_memory=False)
        except (pd.errors.ParserError, UnicodeDecodeError, OSError):
            # repli avec séparateur ';'
            df = pd.read_csv(fpath, low_memory=False, sep=";")
        dfs.append(df)
        logger.info(
            "lu %s -> %d lignes, %d colonnes",
            fpath.name,
            len(df),
            len(df.columns),
        )

    combined = pd.concat(dfs, ignore_index=True, sort=False)

    before = len(combined)
    if primary_key and primary_key in combined.columns:
        combined = combined.drop_duplicates(subset=[primary_key])
        logger.info(
            "suppression de %d doublons sur la clé %s",
            before - len(combined),
            primary_key,
        )
    else:
        combined = combined.drop_duplicates()
        logger.info(
            "suppression de %d doublons (général)",
            before - len(combined),
        )

    if output_file is None:
        name = f"cleaned_{year}" if year is not None else "cleaned_all"
        output_file = cleaned_dir / f"{name}.csv"
    output_path = Path(output_file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)
    logger.info(
        "fichier combiné sauvegardé : %s (%d lignes)",
        output_path,
        len(combined),
    )

    return output_path


if __name__ == "__main__":
    # fusion pour 2023
    OUT_2023 = merge_cleaned_year(
        2023,
        cleaned_dir=Path(__file__).parents[2] / "data" / "cleaned",
        primary_key="acc_id",
    )
    print(f"saved combined file 2023: {OUT_2023}")

    # fusion pour 2021
    OUT_2021 = merge_cleaned_year(
        2021,
        cleaned_dir=Path(__file__).parents[2] / "data" / "cleaned",
        primary_key="acc_id",
    )
    print(f"saved combined file 2021: {OUT_2021}")
