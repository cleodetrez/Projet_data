"""Nettoyage usagers 2021 : normalisation colonnes + ajout age_group."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "usagers-2021.csv"
OUT = ROOT / "data" / "cleaned" / "usager_clean_2021.csv"

KEEP = ["Num_Acc", "sexe", "an_nais", "trajet"]

def clean_usager_2021() -> pd.DataFrame:
    """Nettoie usagers 2021: garde Num_Acc, sexe, an_nais, trajet."""
    if not RAW.exists():
        raise FileNotFoundError(f"Fichier brut usagers manquant: {RAW}")
    df = pd.read_csv(RAW, sep=";", low_memory=False)

    cols_present = [c for c in KEEP if c in df.columns]
    df = df[cols_present].copy()

    # Conserver uniquement les colonnes demandées et lignes avec Num_Acc non nul
    if "Num_Acc" in df.columns:
        df = df[df["Num_Acc"].notna()]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} usagers nettoyés 2021")
    return df

if __name__ == "__main__":
    clean_usager_2021()
