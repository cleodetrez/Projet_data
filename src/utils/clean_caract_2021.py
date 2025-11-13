"""nettoie le csv caracteristiques 2021 et ajoute colonnes temporelles."""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "caracteristiques-2021.csv"
OUT = ROOT / "data" / "cleaned" / "caract_clean_2021.csv"


def parse_hrmn(value) -> str | float:
    """normalise une heure HRMN en 'HH:MM' (retourne np.nan si invalide)."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()

    # cas direct "HH:MM"
    if ":" in s:
        parts = s.split(":")
        if len(parts) >= 2:
            hh = parts[0].zfill(2)
            mm = parts[1].zfill(2)
            return f"{hh}:{mm}"

    # extraire les chiffres et fabriquer HH:MM
    digits = re.findall(r"\d+", s)
    token = digits[0] if digits else ""
    if len(token) >= 4:
        token = token[-4:]
    hh = mm = None
    if len(token) == 4:
        hh, mm = token[:2], token[2:]
    elif len(token) == 3:
        hh, mm = token[0], token[1:]
    elif len(token) == 2:
        hh, mm = token, "00"
    elif len(token) == 1:
        hh, mm = token, "00"

    return f"{str(hh).zfill(2)}:{str(mm).zfill(2)}" if hh is not None else np.nan


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
    if "lat" in df.columns and "lon" not in df.columns and "long" in df.columns:
        rename_map["long"] = "lon"
    
    df = df.rename(columns=rename_map)

    # colonnes finales à garder
    wanted = [
        "acc_id", "annee", "mois", "jour", "heure",
        "lat", "lon", "dep", "com"
    ]
    final_cols = [c for c in wanted if c in df.columns]
    final = df[final_cols].dropna(subset=["lat", "lon"])

    OUT.parent.mkdir(exist_ok=True, parents=True)
    final.to_csv(OUT, index=False)

    print(f"{len(final)} accidents nettoyés pour 2021")
    return final


if __name__ == "__main__":
    clean_caracteristiques()
