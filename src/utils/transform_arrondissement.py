"""transformation des codes d'arrondissement vers codes insee commune."""

from __future__ import annotations

import warnings

import pandas as pd

warnings.filterwarnings("ignore")

print("chargement des données...")

# chargement des deux csv
# le fichier `caract_clean.csv` peut utiliser un séparateur détecté automatiquement
try:
    df_accidents = pd.read_csv(
        "data/cleaned/caract_clean_2023.csv",
        sep=None,
        engine="python",
    )
except (OSError, UnicodeDecodeError, pd.errors.ParserError):
    # repli si la détection échoue
    df_accidents = pd.read_csv("data/cleaned/caract_clean_2023.csv")

df_arrondissements = pd.read_csv(
    "data/cleaned/communes_avec_arrondissements.csv",
    sep=";",
)

# debug: afficher les colonnes trouvées
print(f"colonnes accidents: {list(df_accidents.columns)}")

print(f"accidents: {len(df_accidents)} lignes")
print(f"arrondissements: {len(df_arrondissements)} lignes")

# créer un dictionnaire de mapping: code_postal_arrondissement -> code_insee_commune
mapping_dict: dict[str, str] = {}
for _, row in df_arrondissements.iterrows():
    code_postal = str(row["code_postal_arrondissement"])
    code_insee = str(row["code_insee_commune"]).zfill(5)
    mapping_dict[code_postal] = code_insee

print(f"\ndictionnaire de mapping créé avec {len(mapping_dict)} entrées")
print("   exemples:")
for code in ["75101", "75116", "13201", "13055", "69301"]:
    if code in mapping_dict:
        print(f"   - {code} -> {mapping_dict[code]}")

# transformer la colonne 'com' dans le csv accidents
df_accidents["com_original"] = df_accidents["com"].astype(str)
df_accidents["com"] = df_accidents["com"].astype(str).apply(
    lambda x: mapping_dict.get(x, x)
)

print("\ntransformation appliquée...")

# comparer avant/après
changes = (df_accidents["com_original"] != df_accidents["com"]).sum()
print(f"   - lignes modifiées: {changes}")

# afficher quelques exemples de transformations
modified = df_accidents[df_accidents["com_original"] != df_accidents["com"]]
if not modified.empty:
    print("\nexemples de transformations:")
    orig_uniques = modified["com_original"].unique()[:10]
    new_uniques = modified["com"].unique()[:10]
    for orig, new in zip(orig_uniques, new_uniques):
        print(f"   - {orig} -> {new}")

# sauvegarder le csv transformé
df_accidents_transformed = df_accidents.drop(columns=["com_original"])
df_accidents_transformed.to_csv("caract-2023-TRANSFORMED.csv", sep=";", index=False)

print("\ncsv transformé sauvegardé: caract-2023-TRANSFORMED.csv")

# statistiques
with_coords = df_accidents_transformed.dropna(subset=["lat_acc", "lon_acc"]).shape[0]
print("\nstatistiques:")
print(f"   - total lignes: {len(df_accidents_transformed)}")
print(f"   - communes uniques: {df_accidents_transformed['com'].nunique()}")
print(f"   - avec coordonnées valides: {with_coords}")
