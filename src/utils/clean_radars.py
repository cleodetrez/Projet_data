clean_data.py
"""
- delta_v = mesure - limite
- extrait heure depuis la date
- convertit position → lat/lon
sauvegarde : radars_delta_clean.csv
"""
from pathlib import Path
import pandas as pd
import pyproj
import re


ROOT  = Path(__file__).resolve().parents[2]
RAW_R = ROOT / "data/raw/radars-2023.csv"
OUT   = ROOT / "data/cleaned/radars_delta_clean.csv"


project = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)


def clean_radars():
    df = pd.read_csv(RAW_R, sep=";", low_memory=False)




    df["delta_v"] = df["mesure"] - df["limite"]   # >0 = excès
   
    df["datetime"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce") #heure depuis la date
    df["heure"]     = df["datetime"].dt.hour


    # parse position robustly (handle NaN, different separators, and WKT like 'POINT(x y)')
    def _parse_position(p):
        if pd.isna(p):
            return (None, None)
        if isinstance(p, str):
            s = p.strip()
            # extract numbers from common formats
            nums = re.findall(r"[-+]?\d*\.?\d+", s)
            if len(nums) >= 2:
                try:
                    return float(nums[0]), float(nums[1])
                except ValueError:
                    return (None, None)
        return (None, None)


    coords = df["position"].apply(_parse_position)
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


    final = df[["delta_v", "heure", "lat", "lon", "mesure", "limite"]].dropna() #colonnes finales en enlevant les na


    OUT.parent.mkdir(exist_ok=True)
    final.to_csv(OUT, index=False)
    print(f"{len(final)} radars donne delta_v min={final.delta_v.min()} max={final.delta_v.max()}")
    return final


if __name__ == "__main__":
    clean_radars()
