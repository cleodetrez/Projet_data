"""
Configuration minimale du projet.
Contient les URLs des jeux de données et quelques chemins configurables.
Les valeurs peuvent être surchargées via les variables d'environnement DATA_URL1, DATA_URL2, DATA_DIR.
"""
import os
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent 

URL1_DEFAULT = "https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/#/resources/104dbb32-704f-4e99-a71e-43563cb604f2"
URL2_DEFAULT = "https://www.data.gouv.fr/datasets/jeux-de-donnees-des-vitesses-relevees-par-les-voitures-radars-a-conduite-externalisee/#/resources/52200d61-5e80-4a4e-999f-6e1c184fa122"

url1: str = os.getenv("DATA_URL1", URL1_DEFAULT)
url2: str = os.getenv("DATA_URL2", URL2_DEFAULT)

DATA_DIR: Path = Path(os.getenv("DATA_DIR", ROOT / "data"))
RAW_DIR: Path = DATA_DIR / "raw"

def get_all() -> Dict[str, str]:
    """Retourne un dict simple des valeurs de config (utile pour debug/tests)."""
    return {
        "url1": url1,
        "url2": url2,
        "data_dir": str(DATA_DIR),
        "raw_dir": str(RAW_DIR),
    }