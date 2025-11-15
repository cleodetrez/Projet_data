"""nettoie le csv radars 2021 et calcule delta_v + coordonnées wgs84."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyproj
from .common_functions import parse_hrmn, parse_position

ROOT = Path(__file__).resolve().parents[2]
RAW_R = ROOT / "data" / "raw" / "radars-2021.csv"
OUT = ROOT / "data" / "cleaned" / "radars_delta_clean_2021.csv"

PROJECT = pyproj.Transformer.from_crs(
    "EPSG:2154", "EPSG:4326", always_xy=True
)



def enrich_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """crée les colonnes annee/mois/jour/heure/datetime selon les données présentes."""
    df = df.copy()

    if "date" in df.columns:
        parsed = pd.to_datetime(
            df["date"], dayfirst=True, errors="coerce"
        )
        df["datetime"] = parsed
        mask = parsed.notna()
        df.loc[mask, "annee"] = parsed.dt.year
        df.loc[mask, "mois"] = parsed.dt.month
        df.loc[mask, "jour"] = parsed.dt.day
        df.loc[mask, "heure"] = parsed.dt.strftime("%H:%M")
        return df

    # fallback: colonne hrmn
    if "hrmn" in df.columns:
        df["heure"] = df["hrmn"].apply(parse_hrmn)
    else:
        df["heure"] = pd.NA

    df["datetime"] = pd.NaT
    df["annee"] = pd.NA
    df["mois"] = pd.NA
    df["jour"] = pd.NA
    return df


def clean_radars() -> pd.DataFrame:
    """lit le csv, calcule delta_v, normalise date/heure et projette en wgs84."""
    df = pd.read_csv(RAW_R, sep=";", low_memory=False)

    # delta_v > 0 => excès
    if {"mesure", "limite"}.issubset(df.columns):
        df["delta_v"] = df["mesure"] - df["limite"]
    else:
        df["delta_v"] = pd.NA

    # enrichir les champs temporels
    df = enrich_datetime(df)

    # parse positions (x, y) puis convertit en (lon, lat)
    coords = df["position"].apply(parse_position) if "position" in df.columns else []
    if len(coords) > 0:
        df["x_raw"] = [t[0] for t in coords]
        df["y_raw"] = [t[1] for t in coords]
        mask = df["x_raw"].notna() & df["y_raw"].notna()
        if not mask.any():
            raise RuntimeError("aucune position valide trouvée dans 'position'")

        x_vals = df.loc[mask, "x_raw"].tolist()
        y_vals = df.loc[mask, "y_raw"].tolist()
        lon, lat = PROJECT.transform(x_vals, y_vals)

        df["lon"] = float("nan")
        df["lat"] = float("nan")
        df.loc[mask, "lon"] = lon
        df.loc[mask, "lat"] = lat
    else:
        # colonnes absentes : garder lat/lon vides
        df["lon"] = float("nan")
        df["lat"] = float("nan")

    # colonnes finales si présentes
    wanted = [
        "delta_v", "annee", "mois", "jour", "heure",
        "lat", "lon", "mesure", "limite",
    ]
    final_cols = [c for c in wanted if c in df.columns]
    final = df[final_cols].dropna(subset=["lat", "lon"])

    OUT.parent.mkdir(exist_ok=True, parents=True)
    final.to_csv(OUT, index=False)

    # résumé
    min_delta = final["delta_v"].min() if "delta_v" in final.columns else None
    max_delta = final["delta_v"].max() if "delta_v" in final.columns else None
    print(
        f"{len(final)} radars 2021, delta_v min={min_delta}, max={max_delta}"
    )

    return final


if __name__ == "__main__":
    clean_radars()
