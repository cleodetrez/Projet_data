import os
from pathlib import Path

root = Path(__file__).resolve().parent 

# URLs pour 2023
caract_csv_url = "https://www.data.gouv.fr/fr/datasets/r/104dbb32-704f-4e99-a71e-43563cb604f2"
radar_csv_url = "https://www.data.gouv.fr/fr/datasets/r/52200d61-5e80-4a4e-999f-6e1c184fa122"

# URLs pour 2021
caract_csv_url_2021 = "https://www.data.gouv.fr/api/1/datasets/r/85cfdc0c-23e4-4674-9bcd-79a970d7269b"
radar_csv_url_2021 = "https://www.data.gouv.fr/api/1/datasets/r/8b6cd190-3b66-43a8-b609-ce130019069f"

data_dir = Path(os.getenv("data_dir", root / "data"))
raw_dir = data_dir / "raw"