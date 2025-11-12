"""nettoie le csv radars 2023 et calcule delta_v + coordonnées wgs84."""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd
import pyproj

ROOT = Path(__file__).resolve().parents[2]
RAW_R = ROOT / "data" / "raw" / "radars-2023.csv"
OUT = ROOT / "data" / "cleaned" / "radars_delta_clean.csv"

PROJECT = pyproj.Transformer.from_crs(
    "EPSG:2154", "EPSG:4326", always_xy=True
)


def parse_hrmn(value) -> str | float:
    """normalise une heure HRMN en 'HH:MM' (retourne np.nan si invalide)."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()

    # cas direct "HH:MM"
    if ":" in s:
        parts = s.split(":")
        if len(parts) >= 2:
            hh = parts[0].zfill(2)
            mm = parts[1].zfill(2)
            return f"{hh}:{mm}"

    # extraire les chiffres et fabriquer HH:MM
    digits = re.findall(r"\d+", s)
    token = digits[0] if digits else ""
    if len(token) >= 4:
        token = token[-4:]
    hh = mm = None
    if len(token) == 4:
        hh, mm = token[:2], token[2:]
    elif len(token) == 3:
        hh, mm = token[0], token[1:]
    elif len(token) == 2:
        hh, mm = token, "00"
    elif len(token) == 1:
        hh, mm = token, "00"

    return f"{str(hh).zfill(2)}:{str(mm).zfill(2)}" if hh is not None else np.nan


def parse_position(p) -> tuple[float | None, float | None]:
    """extrait (x, y) flottants d'une chaîne, sinon (None, None)."""
    if pd.isna(p):
        return (None, None)
    if isinstance(p, str):
        s = p.strip()
        nums = re.findall(r"[-+]?\d*\.?\d+", s)
        if len(nums) >= 2:
            try:
                return float(nums[0]), float(nums[1])
            except ValueError:
                return (None, None)
    return (None, None)


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
    if coords:
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

    # résumé (formaté court pour éviter > 100 chars)
    min_delta = final["delta_v"].min() if "delta_v" in final.columns else None
    max_delta = final["delta_v"].max() if "delta_v" in final.columns else None
    print(
        f"{len(final)} radars, delta_v min={min_delta}, max={max_delta}"
    )

    return final


if __name__ == "__main__":
    clean_radars()
