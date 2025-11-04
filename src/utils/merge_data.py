from sklearn.neighbors import BallTree
import numpy as np


def merge_accidents_radars(df_acc, df_radar, max_distance_km=1.0):
    # Convertir en radians
    coords_acc = np.radians(df_acc[['lat', 'long']].values)
    coords_radar = np.radians(df_radar[['lat', 'long']].values)


    # Arbre spatial
    tree = BallTree(coords_radar, metric='haversine')


    # Rayon en radians (1 km ≈ 0.008 radians)
    radius = max_distance_km / 6371.0


    # Recherche des radars à moins de 1 km
    indices = tree.query_radius(coords_acc, r=radius)


    # Ajouter un identifiant unique
    df_acc = df_acc.reset_index(drop=True)
    df_acc['index_acc'] = df_acc.index


    # Expansion des accidents avec leurs radars proches
    rows = []
    for i, radar_idx in enumerate(indices):
        if len(radar_idx) > 0:
            for r in radar_idx:
                rows.append({
                    'index_acc': i,
                    'radar_idx': r
                })


    # DataFrame de liaison
    df_link = pd.DataFrame(rows)


    # Merge avec les vraies données
    df_link = df_link.merge(df_acc, on='index_acc')
    df_link = df_link.merge(df_radar.reset_index().rename(columns={'index': 'radar_idx'}), on='radar_idx')


    df_link = df_link[df_link['date_x'] == df_link['date_y']] #


    # Suppression des doublons (accident_id unique)
    #df_link = df_link.drop_duplicates(subset=['accident_id'])


    return df_link[['accident_id', 'date_x', 'lat_x', 'long_x', 'vitesse_mesuree', 'vitesse_limite']]
