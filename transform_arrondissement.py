"""
test vraiment test
"""

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("Chargement des données...")

# chargement des deux csv
# Le fichier `caract_clean.csv` utilise des virgules comme séparateur; on laisse pandas détecter
try:
    df_accidents = pd.read_csv('data/cleaned/caract_clean.csv', sep=None, engine='python')
except Exception:
    # fallback si détection échoue
    df_accidents = pd.read_csv('data/cleaned/caract_clean.csv')

df_arrondissements = pd.read_csv('data/cleaned/communes_avec_arrondissements.csv', sep=';')

# Debug: afficher les colonnes trouvées (aide au diagnostic)
print(f"Colonnes accidents: {list(df_accidents.columns)}")

print(f"Accidents: {len(df_accidents)} lignes")
print(f"Arrondissements: {len(df_arrondissements)} lignes")

# Créer un dictionnaire de mapping: code_postal_arrondissement devient code_insee_commune
mapping_dict = {}
for idx, row in df_arrondissements.iterrows():
    code_postal = str(row['code_postal_arrondissement'])
    code_insee = str(row['code_insee_commune']).zfill(5)
    mapping_dict[code_postal] = code_insee

print(f"\n Dictionnaire de mapping créé avec {len(mapping_dict)} entrées")
print(f"   Exemples:")
for code in ['75101', '75116', '13201', '13055', '69301']:
    if code in mapping_dict:
        print(f"   - {code} -> {mapping_dict[code]}")

# Transformer la colonne 'com' dans le CSV accidents
df_accidents['com_original'] = df_accidents['com'].astype(str)
df_accidents['com'] = df_accidents['com'].astype(str).apply(
    lambda x: mapping_dict.get(x, x)  # Si trouve dans mapping, remplace, sinon garde l'original
)

print(f"\n Transformation appliquée...")

# Comparer avant/après
changes = (df_accidents['com_original'] != df_accidents['com']).sum()
print(f"   • Lignes modifiées: {changes}")

# Afficher les communes modifiées
modified = df_accidents[df_accidents['com_original'] != df_accidents['com']]
if len(modified) > 0:
    print(f"\n Exemples de transformations:")
    for orig, new in zip(modified['com_original'].unique()[:10], modified['com'].unique()[:10]):
        print(f"   - {orig} -> {new}")

# Sauvegarder le CSV transformé
df_accidents_transformed = df_accidents.drop(columns=['com_original'])
df_accidents_transformed.to_csv('caract-2023-TRANSFORMED.csv', sep=';', index=False)

print(f"\n CSV transformé sauvegardé: caract-2023-TRANSFORMED.csv")

# Statistiques
print(f"\n Statistiques:")
print(f"   • Total lignes: {len(df_accidents_transformed)}")
print(f"   • Communes uniques: {df_accidents_transformed['com'].nunique()}")
print(f"   • Avec coordonnées valides: {df_accidents_transformed.dropna(subset=['lat_acc', 'lon_acc']).shape[0]}")