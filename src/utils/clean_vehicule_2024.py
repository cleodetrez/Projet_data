"""
clean_vehicule_2024.py : Nettoie le fichier vehicules 2024
"""
from pathlib import Path
try:
    # When executed as part of the package (e.g., via main.py)
    from .common_functions import clean_subset_csv
except ImportError:  # pragma: no cover - fallback for direct script execution
    # When executed directly: python src/utils/clean_vehicule_2024.py
    import sys
    ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
    # Add project root so 'src' is importable as a top-level package
    sys.path.insert(0, str(ROOT_FOR_IMPORT))
    from src.utils.common_functions import clean_subset_csv  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

KEEP = ["Num_Acc", "catv", "motor"]

def clean_vehicule_2024():
    """Nettoie vehicules-2024.csv : garde Num_Acc, catv, motor."""
    raw_path = RAW_DIR / "vehicules-2024.csv"
    cleaned_path = CLEAN_DIR / "vehicule_clean_2024.csv"

    if not raw_path.exists():
        print(f"Fichier brut manquant : {raw_path}")
        return

    rows = clean_subset_csv(raw_path, cleaned_path, KEEP, sep=";")
    print(f"vehicule_clean_2024.csv cree : {rows} lignes")

if __name__ == "__main__":
    clean_vehicule_2024()
