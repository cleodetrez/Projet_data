import sqlite3

conn = sqlite3.connect('bdd/database.db')
cursor = conn.cursor()

# Lister les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables disponibles:")
for table in tables:
    print(f"  - {table}")

# Vérifier la structure de caract_usager_vehicule_2022
if 'caract_usager_vehicule_2022' in tables:
    print("\nStructure de caract_usager_vehicule_2022:")
    cursor.execute("PRAGMA table_info(caract_usager_vehicule_2022)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Vérifier si grav existe
    cursor.execute("SELECT COUNT(*) FROM caract_usager_vehicule_2022")
    print(f"\nNombre de lignes: {cursor.fetchone()[0]}")
    
    # Essayer de sélectionner grav
    try:
        cursor.execute("SELECT grav, COUNT(*) FROM caract_usager_vehicule_2022 GROUP BY grav")
        print("\nDistribution de grav:")
        for row in cursor.fetchall():
            print(f"  grav={row[0]}: {row[1]} lignes")
    except Exception as e:
        print(f"\nErreur lors de la sélection de grav: {e}")

conn.close()
