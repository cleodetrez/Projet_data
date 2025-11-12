import json

with open('communes.geojson') as f:
    g = json.load(f)

print(f'Type: {g.get("type")}')
print(f'Nombre de features: {len(g.get("features",[]))}')

if g.get("features"):
    print(f'Propriétés: {list(g["features"][0]["properties"].keys())}')
    print(f'Exemple feature: {g["features"][0]["geometry"]["type"]}')
