"""
config
"""
import os
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent 

CARACT2023 = "https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/#/resources/104dbb32-704f-4e99-a71e-43563cb604f2"
RADAR2023 = "https://www.data.gouv.fr/datasets/jeux-de-donnees-des-vitesses-relevees-par-les-voitures-radars-a-conduite-externalisee/#/resources/52200d61-5e80-4a4e-999f-6e1c184fa122"

caract2023: str = os.getenv("DATA_caract2023", CARACT2023)
radar2023: str = os.getenv("DATA_radar2023", RADAR2023)

DATA_DIR: Path = Path(os.getenv("DATA_DIR", ROOT / "data"))
RAW_DIR: Path = DATA_DIR / "raw"

def get_all() -> Dict[str, str]:
    """Retourne un dict simple des valeurs de config"""
    return {
        "caract2023": caract2023,
        "radar2023": radar2023,
        "data_dir": str(DATA_DIR),
        "raw_dir": str(RAW_DIR),
    }