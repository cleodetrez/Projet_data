"""
clean_vehicule_2020.py : Nettoie le fichier vehicules 2020
"""
from pathlib import Path
from .common_functions import clean_subset_csv

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

KEEP = ["Num_Acc", "catv", "motor"]

def clean_vehicule_2020():
    """Nettoie vehicules-2020.csv : garde Num_Acc, catv, motor."""
    raw_path = RAW_DIR / "vehicules-2020.csv"
    cleaned_path = CLEAN_DIR / "vehicule_clean_2020.csv"

    if not raw_path.exists():
        print(f"Fichier brut manquant : {raw_path}")
        return

    rows = clean_subset_csv(raw_path, cleaned_path, KEEP, sep=";")
    print(f"vehicule_clean_2020.csv cree : {rows} lignes")

if __name__ == "__main__":
    clean_vehicule_2020()
