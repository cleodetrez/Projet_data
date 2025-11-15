import os
from pathlib import Path

root = Path(__file__).resolve().parent 

# URLs pour 2023
caract_csv_url = "https://www.data.gouv.fr/fr/datasets/r/104dbb32-704f-4e99-a71e-43563cb604f2"
radar_csv_url = "https://www.data.gouv.fr/fr/datasets/r/52200d61-5e80-4a4e-999f-6e1c184fa122"

# URLs pour 2021
caract_csv_url_2021 = "https://www.data.gouv.fr/api/1/datasets/r/85cfdc0c-23e4-4674-9bcd-79a970d7269b"
radar_csv_url_2021 = "https://www.data.gouv.fr/api/1/datasets/r/8b6cd190-3b66-43a8-b609-ce130019069f"

# URLs pour 2020
caract_csv_url_2020 = "https://www.data.gouv.fr/api/1/datasets/r/07a88205-83c1-4123-a993-cba5331e8ae0"

# URLs pour 2022
caract_csv_url_2022 = "https://www.data.gouv.fr/api/1/datasets/r/5fc299c0-4598-4c29-b74c-6a67b0cc27e7"

# URLs pour 2024
caract_csv_url_2024 = "https://www.data.gouv.fr/api/1/datasets/r/83f0fb0e-e0ef-47fe-93dd-9aaee851674a"

# URLs usager (ajout progressif par année)
usager_csv_url_2024 = "https://www.data.gouv.fr/api/1/datasets/r/f57b1f58-386d-4048-8f78-2ebe435df868"
usager_csv_url_2023 = "https://www.data.gouv.fr/api/1/datasets/r/68848e2a-28dd-4efc-9d5f-d512f7dbe66f"
usager_csv_url_2022 = "https://www.data.gouv.fr/api/1/datasets/r/62c20524-d442-46f5-bfd8-982c59763ec8"
usager_csv_url_2021 = "https://www.data.gouv.fr/api/1/datasets/r/ba5a1956-7e82-41b7-a602-89d7dd484d7a"
usager_csv_url_2020 = "https://www.data.gouv.fr/api/1/datasets/r/78c45763-d170-4d51-a881-e3147802d7ee"

# URLs vehicule (ajout progressif par année)
vehicule_csv_url_2023 = "https://www.data.gouv.fr/api/1/datasets/r/146a42f5-19f0-4b3e-a887-5cd8fbef057b"
vehicule_csv_url_2022 = "https://www.data.gouv.fr/api/1/datasets/r/c9742921-4427-41e5-81bc-f13af8bc31a0"
vehicule_csv_url_2021 = "https://www.data.gouv.fr/api/1/datasets/r/0bb5953a-25d8-46f8-8c25-b5c2f5ba905e"
vehicule_csv_url_2020 = "https://www.data.gouv.fr/api/1/datasets/r/a66be22f-c346-49af-b196-71df24702250"

data_dir = Path(os.getenv("data_dir", root / "data"))
raw_dir = data_dir / "raw"