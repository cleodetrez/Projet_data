"""
test encore test
"""

import pandas as pd
import json
import folium
import warnings
warnings.filterwarnings('ignore')

# Charger le CSV
df = pd.read_csv('caract-2023.csv', sep=';')

# Nettoyer les données
df['lat'] = pd.to_numeric(df['lat'].astype(str).str.replace(',', '.').str.strip(), errors='coerce')
df['long'] = pd.to_numeric(df['long'].astype(str).str.replace(',', '.').str.strip(), errors='coerce')
df['com'] = df['com'].astype(str).str.zfill(5)

# Supprimer les lignes sans coordonnées
df_clean = df.dropna(subset=['lat', 'long'])

print(f"✓ Données: {len(df)} lignes, {len(df_clean)} avec coordonnées valides")

# Compter les occurrences par commune
commune_counts = df_clean.groupby('com').agg({
    'lat': 'first',
    'long': 'first',
    'Num_Acc': 'count'
}).rename(columns={'Num_Acc': 'count'})

commune_counts = commune_counts.dropna(subset=['lat', 'long'])

print(f"✓ {len(commune_counts)} communes trouvées")

# Créer le fichier com.json
com_data = {}
for com_code, row in commune_counts.iterrows():
    com_data[com_code] = {
        'lat': float(row['lat']),
        'long': float(row['long']),
        'count': int(row['count'])
    }

with open('com.json', 'w', encoding='utf-8') as f:
    json.dump(com_data, f, ensure_ascii=False, indent=2)

print(f" com.json créé avec {len(com_data)} communes")

# Charger le GeoJSON
print("\n Chargement du GeoJSON...")
try:
    with open('communes.geojson', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    print(f" {len(geojson_data['features'])} communes GeoJSON chargées")
except Exception as e:
    print(f" Erreur: {e}")
    exit()

# Normaliser les couleurs
min_count = commune_counts['count'].min()
max_count = commune_counts['count'].max()

def get_color_bin(count):
    """Retourne une couleur selon des bins logarithmiques"""
    # Bins logarithmiques personnalisés
    if count == 0:
        return '#CCCCCC'  # Gris pour 0
    elif count < 5:
        return '#FFFF99'  # Jaune clair (0-5)
    elif count < 15:
        return '#FFFF00'  # Jaune (5-15)
    elif count < 30:
        return '#FFD700'  # Orange clair (15-30)
    elif count < 60:
        return '#FFA500'  # Orange (30-60)
    elif count < 120:
        return '#FF8C00'  # Orange foncé (60-120)
    elif count < 200:
        return '#FF6347'  # Tomato rouge (120-200)
    elif count < 300:
        return '#FF4500'  # Orange-rouge (200-300)
    else:
        return '#FF0000'  # Rouge intense (300+)
    
    return '#CCCCCC'

# Créer la carte
center_lat = 46.2276
center_long = 2.2137

m = folium.Map(
    location=[center_lat, center_long],
    zoom_start=5,
    tiles='OpenStreetMap'
)

print("\n Génération de la choroplèthe...")

# Dictionnaire pour accès rapide aux données
accident_dict = commune_counts['count'].to_dict()

# Ajouter chaque feature GeoJSON à la carte
matched_count = 0
zero_count = 0
for idx, feature in enumerate(geojson_data['features']):
    if idx % 5000 == 0:
        print(f"   Traitement: {idx}/{len(geojson_data['features'])}...")
    
    try:
        properties = feature.get('properties', {})
        com_code = properties.get('code', '')
        com_name = properties.get('nom', '')
        
        # Récupérer le compte d'accidents, 0 si pas présent
        count = accident_dict.get(com_code, 0)
        color = get_color_bin(count)
        
        # Créer le GeoJson avec style (sans popup pour plus de vitesse)
        folium.GeoJson(
            data=feature,
            style_function=lambda x, c=color: {
                'fillColor': c,
                'color': '#333333',
                'weight': 0.5,
                'fillOpacity': 0.8
            },
            tooltip=f"<b>{com_name}</b><br/>Code: {com_code}<br/>Accidents: {int(count)}"
        ).add_to(m)
        
        matched_count += 1
        if count == 0:
            zero_count += 1
    except Exception as e:
        pass

print(f"✓ {matched_count} communes affichées sur la carte ({zero_count} sans accidents en gris)")

# Ajouter une légende
legend_html = '''
<div style="position: fixed; 
     bottom: 50px; right: 50px; width: 320px; height: 380px; 
     background-color: white; border:3px solid #333; z-index:9999; 
     font-size:14px; padding: 15px; border-radius: 8px;
     box-shadow: 3px 3px 10px rgba(0,0,0,0.4)">
     
<p style="margin:0; font-weight: bold; text-align: center; font-size: 16px; color: #333;">
  CHOROPLÈTHE - Accidents 2023
</p>
<hr style="margin: 10px 0; border: none; border-top: 2px solid #ff6347;">

<p style="margin: 10px 0; font-size: 12px; font-weight: bold; color: #333;">Nombre d'accidents:</p>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #CCCCCC; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">0 accident (aucun)</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FFFF99; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">1-5 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FFFF00; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">5-15 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FFD700; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">15-30 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FFA500; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">30-60 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FF8C00; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">60-120 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FF6347; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">120-200 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FF4500; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;">200-300 accidents</span>
</div>

<div style="display: flex; align-items: center; margin: 8px 0;">
  <div style="width: 25px; height: 25px; background-color: #FF0000; border: 2px solid #333; margin-right: 10px;"></div>
  <span style="font-size: 12px;"><b>300+ accidents</b></span>
</div>

<hr style="margin: 10px 0; border: none; border-top: 1px solid #ccc;">

<p style="margin: 5px 0; font-size: 11px; color: #666; font-style: italic;">
  Cliquez sur une zone pour voir les détails
</p>
</div>
'''

m.get_root().html.add_child(folium.Element(legend_html))

# Sauvegarder la carte
m.save('radars_map.html')
print(f"\n✓ Carte choroplèthe générée: radars_map.html")
print(f"\n Statistiques:")
print(f"   • Minimum: {int(min_count)} accident(s)")
print(f"   • Maximum: {int(max_count)} accidents")
print(f"   • Moyenne: {commune_counts['count'].mean():.1f} accidents/commune")
print(f"   • Total: {commune_counts['count'].sum()} accidents")

print(f"\n🏆 Top 10 des communes les plus accidentées:")
top10 = commune_counts.sort_values('count', ascending=False).head(10)
for idx, (com_code, row) in enumerate(top10.iterrows(), 1):
    print(f"   {idx}. Commune {com_code}: {int(row['count'])} accidents")