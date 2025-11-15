"""Nettoie le csv radars 2023 et calcule delta_v + coordonnées wgs84."""

from pathlib import Path
import pandas as pd
import pyproj
from .common_functions import parse_hrmn, parse_position

ROOT  = Path(__file__).resolve().parents[2]
RAW_R = ROOT / "data/raw/radars-2023.csv"
OUT   = ROOT / "data/cleaned/radars_delta_clean_2023.csv"

project = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)

def clean_radars():
    """Nettoie radars 2023: calcule delta_v et projette en WGS84."""
    df = pd.read_csv(RAW_R, sep=";", low_memory=False)

    df["delta_v"] = df["mesure"] - df["limite"]   # >0 = excès

    # --- Priorité à la colonne 'date' pour année/mois/jour/heure (HH:MM) ---
    if "date" in df.columns:
        parsed_dt = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df["datetime"] = parsed_dt

        # remplir année/mois/jour/heure uniquement pour les lignes parsées
        df.loc[parsed_dt.notna(), "annee"] = parsed_dt.dt.year
        df.loc[parsed_dt.notna(), "mois"] = parsed_dt.dt.month
        df.loc[parsed_dt.notna(), "jour"] = parsed_dt.dt.day
        df.loc[parsed_dt.notna(), "heure"] = parsed_dt.dt.strftime("%H:%M")
    else:
        # si pas de 'date', tenter de parser une colonne 'hrmn' si elle existe (fallback)
        if "hrmn" in df.columns:
            df["heure"] = df["hrmn"].apply(parse_hrmn)
        else:
            # sinon laisser heure vide / NaN
            df["heure"] = pd.NA
            df["datetime"] = pd.NaT
            df["annee"] = pd.NA
            df["mois"] = pd.NA
            df["jour"] = pd.NA

    # parse position robustly (handle NaN, different separators, and WKT like 'POINT(x y)')
    coords = df["position"].apply(parse_position)
    df["x_raw"] = coords.apply(lambda t: t[0])
    df["y_raw"] = coords.apply(lambda t: t[1])

    # keep only rows with valid numeric coordinates
    mask = df["x_raw"].notna() & df["y_raw"].notna()
    if not mask.any():
        raise RuntimeError("Aucune position valide trouvée dans 'position'")

    x = df.loc[mask, "x_raw"].tolist()
    y = df.loc[mask, "y_raw"].tolist()

    lon, lat = project.transform(x, y)
    # populate lon/lat, leave NaN where parsing failed
    df["lon"] = float("nan")
    df["lat"] = float("nan")
    df.loc[mask, "lon"] = lon
    df.loc[mask, "lat"] = lat

    # construire le DataFrame final avec année/mois/jour/heure (HH:MM)
    final_cols = [
        "delta_v", "annee", "mois", "jour", "heure",
        "lat", "lon", "mesure", "limite"
    ]
    # s'assurer que seules les colonnes existantes sont sélectionnées
    final_cols = [c for c in final_cols if c in df.columns]
    final = df[final_cols].dropna(subset=["lat", "lon"])

    OUT.parent.mkdir(exist_ok=True)
    final.to_csv(OUT, index=False)
    print(f"{len(final)} radars donne delta_v min={final.delta_v.min()} max={final.delta_v.max()}")
    return final

if __name__ == "__main__":
    clean_radars()
