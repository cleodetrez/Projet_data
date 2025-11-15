"""génère une carte choroplèthe communale à partir des accidents 2023."""

from __future__ import annotations

import json
import sys
import warnings

import folium
import pandas as pd

warnings.filterwarnings("ignore")

# charger le csv
DF = pd.read_csv("caract-2023-TRANSFORMED.csv", sep=";")

# nettoyer les données
DF["lat"] = pd.to_numeric(
    DF["lat"].astype(str).str.replace(",", ".").str.strip(),
    errors="coerce",
)
DF["long"] = pd.to_numeric(
    DF["long"].astype(str).str.replace(",", ".").str.strip(),
    errors="coerce",
)
DF["com"] = DF["com"].astype(str).str.zfill(5)

# supprimer les lignes sans coordonnées
df_clean = DF.dropna(subset=["lat", "long"])

print(f"✓ données: {len(DF)} lignes, {len(df_clean)} avec coordonnées valides")

# compter les occurrences par commune
commune_counts = (
    df_clean.groupby("com")
    .agg({"lat": "first", "long": "first", "Num_Acc": "count"})
    .rename(columns={"Num_Acc": "count"})
)
commune_counts = commune_counts.dropna(subset=["lat", "long"])

print(f"✓ {len(commune_counts)} communes trouvées")

# créer le fichier com.json
com_data: dict[str, dict[str, float | int]] = {}
for com_code, row in commune_counts.iterrows():
    com_data[com_code] = {
        "lat": float(row["lat"]),
        "long": float(row["long"]),
        "count": int(row["count"]),
    }

with open("com.json", "w", encoding="utf-8") as f:
    json.dump(com_data, f, ensure_ascii=False, indent=2)

print(f"com.json créé avec {len(com_data)} communes")

# charger le geojson
print("\nchargement du geojson...")
try:
    with open("communes.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    print(f"{len(geojson_data['features'])} communes geojson chargées")
except (OSError, json.JSONDecodeError) as err:
    print(f"erreur: {err}")
    sys.exit(1)

# normaliser les couleurs
min_count = int(commune_counts["count"].min())
max_count = int(commune_counts["count"].max())


def get_color_bin(value: int) -> str:
    """retourne une couleur selon des bins."""
    # (seuil, couleur)
    bins = [
        (0, "#CCCCCC"),
        (5, "#FFFF99"),
        (15, "#FFFF00"),
        (30, "#FFD700"),
        (60, "#FFA500"),
        (120, "#FF8C00"),
        (200, "#FF6347"),
        (300, "#FF4500"),
    ]
    for threshold, bin_color in bins:
        if value <= threshold:
            return bin_color
    return "#FF0000"


# créer la carte
CENTER_LAT = 46.2276
CENTER_LONG = 2.2137

m = folium.Map(location=[CENTER_LAT, CENTER_LONG], zoom_start=5, tiles="OpenStreetMap")

print("\ngénération de la choroplèthe...")

# dictionnaire pour accès rapide aux données
accident_dict = commune_counts["count"].to_dict()

# ajouter chaque feature geojson à la carte
matched_count = 0
zero_count = 0
for idx, feature in enumerate(geojson_data["features"]):
    if idx % 5000 == 0:
        print(f"   traitement: {idx}/{len(geojson_data['features'])}...")

    try:
        properties = feature.get("properties", {})
        com_code = properties.get("code", "")
        com_name = properties.get("nom", "")

        # récupérer le compte d'accidents, 0 si pas présent
        n_acc = int(accident_dict.get(com_code, 0))
        fill_color = get_color_bin(n_acc)

        # créer le geojson avec style (sans popup pour plus de vitesse)
        folium.GeoJson(
          data=feature,
          style_function=lambda _x, c=fill_color: {
            "fillColor": c,
            "color": "#00000000",  # pas de contour
            "weight": 0,
            "fillOpacity": 0.85,
          },
          tooltip=f"<b>{com_name}</b><br/>code: {com_code}<br/>accidents: {n_acc}",
        ).add_to(m)

        matched_count += 1
        if n_acc == 0:
            zero_count += 1
    except (KeyError, TypeError, ValueError):
        # ignorer les features mal formées
        continue

print(
    f"✓ {matched_count} communes affichées sur la carte "
    f"({zero_count} sans accidents en gris)"
)

# ajouter une légende
LEGEND_HTML = """
<div style="position: fixed;
     bottom: 50px; right: 50px; width: 320px; height: 380px;
     background-color: white; border:3px solid #333; z-index:9999;
     font-size:14px; padding: 15px; border-radius: 8px;
     box-shadow: 3px 3px 10px rgba(0,0,0,0.4)">
<p style="margin:0; font-weight: bold; text-align: center; font-size: 16px; color: #333;">
  choroplèthe - accidents 2023
</p>
<hr style="margin: 10px 0; border: none; border-top: 2px solid #ff6347;">
<p style="margin: 10px 0; font-size: 12px; font-weight: bold; color: #333;">
  nombre d'accidents:
</p>
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
  cliquez sur une zone pour voir les détails
</p>
</div>
"""

m.get_root().html.add_child(folium.Element(LEGEND_HTML))

# sauvegarder la carte
m.save("radars_map.html")
print("\n✓ carte choroplèthe générée: radars_map.html")
print("\nstatistiques:")
print(f"   • minimum: {min_count} accident(s)")
print(f"   • maximum: {max_count} accidents")
print(f"   • moyenne: {commune_counts['count'].mean():.1f} accidents/commune")
print(f"   • total: {commune_counts['count'].sum()} accidents")

print("\ntop 10 des communes les plus accidentées:")
top10 = commune_counts.sort_values("count", ascending=False).head(10)
for idx, (com_code, row) in enumerate(top10.iterrows(), 1):
    print(f"   {idx}. commune {com_code}: {int(row['count'])} accidents")
