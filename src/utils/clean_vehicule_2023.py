"""
clean_vehicule_2023.py : Nettoie le fichier vehicules 2023
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

KEEP = ["Num_Acc", "catv", "motor"]

def clean_vehicule_2023():
    """Nettoie vehicules-2023.csv : garde Num_Acc, catv, motor."""
    raw_path = RAW_DIR / "vehicules-2023.csv"
    cleaned_path = CLEAN_DIR / "vehicule_clean_2023.csv"
    
    if not raw_path.exists():
        print(f"Fichier brut manquant : {raw_path}")
        return
    
    df = pd.read_csv(raw_path, low_memory=False, sep=";")
    
    # Garder les colonnes voulues
    missing = [c for c in KEEP if c not in df.columns]
    if missing:
        print(f"Colonnes manquantes dans vehicules 2023 : {missing}")
        return
    
    df = df[KEEP].copy()
    
    # Retirer les lignes sans Num_Acc
    df = df[df["Num_Acc"].notna()]
    
    df.to_csv(cleaned_path, index=False)
    print(f"vehicule_clean_2023.csv cree : {len(df)} lignes")

if __name__ == "__main__":
    clean_vehicule_2023()
