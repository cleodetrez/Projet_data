import os
from pathlib import Path

root = Path(__file__).resolve().parent 

# on teste l'url de redirection directe pour le caract, comme pour le radar
caract_csv_url = "https://www.data.gouv.fr/fr/datasets/r/104dbb32-704f-4e99-a71e-43563cb604f2"
radar_csv_url = "https://www.data.gouv.fr/fr/datasets/r/52200d61-5e80-4a4e-999f-6e1c184fa122"

data_dir = Path(os.getenv("data_dir", root / "data"))
raw_dir = data_dir / "raw"