"""Nettoyage usagers 2024 : normalisation colonnes + ajout age_group."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "usagers-2024.csv"
OUT = ROOT / "data" / "cleaned" / "usager_clean_2024.csv"

KEEP = ["Num_Acc", "sexe", "an_nais", "trajet"]

def clean_usager_2024() -> pd.DataFrame:
    if not RAW.exists():
        # Tentative de téléchargement automatique si le fichier brut est absent
        try:
            from .get_data import get_usager_2024  # type: ignore
            df = get_usager_2024()
        except Exception as e:
            raise FileNotFoundError(f"Fichier brut usagers manquant et téléchargement impossible: {RAW}") from e
    else:
        df = pd.read_csv(RAW, sep=";", low_memory=False)
    cols_present = [c for c in KEEP if c in df.columns]
    df = df[cols_present].copy()
    if "Num_Acc" in df.columns:
        df = df[df["Num_Acc"].notna()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} usagers nettoyés 2024")
    return df

if __name__ == "__main__":
    clean_usager_2024()
