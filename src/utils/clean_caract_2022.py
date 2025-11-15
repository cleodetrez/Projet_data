"""nettoie le csv caracteristiques 2022 et ajoute colonnes temporelles."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .common_functions import parse_hrmn

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "caracteristiques-2022.csv"
OUT = ROOT / "data" / "cleaned" / "caract_clean_2022.csv"



def clean_caracteristiques() -> pd.DataFrame:
    """lit le csv caracteristiques, ajoute annee/mois/jour/heure."""
    df = pd.read_csv(RAW, sep=";", low_memory=False)

    # parser heure depuis hrmn
    if "hrmn" in df.columns:
        df["heure"] = df["hrmn"].apply(parse_hrmn)
    else:
        df["heure"] = pd.NA

    # extraire année/mois/jour depuis les colonnes existantes
    if "an" in df.columns:
        df["annee"] = df["an"]
    if "mois" in df.columns:
        df["mois"] = df["mois"]
    if "jour" in df.columns:
        df["jour"] = df["jour"]

    # renommer colonnes pour cohérence
    rename_map = {}
    if "Num_Acc" in df.columns:
        rename_map["Num_Acc"] = "acc_id"
    elif "Accident_Id" in df.columns:
        rename_map["Accident_Id"] = "acc_id"
    if "lat" in df.columns and "lon" not in df.columns and "long" in df.columns:
        rename_map["long"] = "lon"

    df = df.rename(columns=rename_map)

    # colonnes finales à garder
    wanted = [
        "acc_id", "annee", "mois", "jour", "heure",
        "lat", "lon", "dep", "com", "agg", "lum", "atm"
    ]
    final_cols = [c for c in wanted if c in df.columns]
    final = df[final_cols].dropna(subset=["lat", "lon"])

    OUT.parent.mkdir(exist_ok=True, parents=True)
    final.to_csv(OUT, index=False)

    print(f"{len(final)} accidents nettoyés pour 2022")
    return final


if __name__ == "__main__":
    clean_caracteristiques()
