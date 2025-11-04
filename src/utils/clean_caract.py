"""
clean_caract.py
Nettoie caracteristiques-2023.csv
on en sort caract_clean.csv
"""
from pathlib import Path
import pandas as pd
import re
import numpy as np


ROOT   = Path(__file__).resolve().parents[2]
RAW_C  = ROOT / "data/raw/caracteristiques-2023.csv"
OUT_C  = ROOT / "data/cleaned/caract_clean.csv"


def clean_caract():
    df = pd.read_csv(RAW_C, sep=";", low_memory=False)


    df = df.dropna(subset=["lat", "long"])


    df["dep"] = df["dep"].astype(str).str.zfill(2)
    df["com"] = df["com"].astype(str).str.zfill(5)
    # hrmn can have many formats ('' , ':00', '0', '0000', '12:34', 1234).
    # Normalize it into hour/minute safely.
    def _parse_hrmn(v):
        if pd.isna(v):
            return (np.nan, np.nan)
        s = str(v).strip()
        if not s:
            return (np.nan, np.nan)
        # common colon-separated form
        if ":" in s:
            parts = s.split(":")
            if len(parts) >= 2:
                h = parts[0].zfill(2)
                m = parts[1].zfill(2)
                return (h, m)
        # extract digits
        digits = re.findall(r"\d+", s)
        if len(digits) == 0:
            return (np.nan, np.nan)
        token = digits[0]
        # if token has 4 or more digits, assume HHMM (take last 4)
        if len(token) >= 4:
            token = token[-4:]
        if len(token) == 4:
            return (token[:2].zfill(2), token[2:].zfill(2))
        if len(token) == 3:
            return (token[0].zfill(2), token[1:].zfill(2))
        if len(token) == 2:
            return (token.zfill(2), "00")
        if len(token) == 1:
            return (token.zfill(2), "00")
        return (np.nan, np.nan)


    parsed = df["hrmn"].apply(_parse_hrmn)
    df["hour"] = parsed.apply(lambda t: t[0])
    df["minute"] = parsed.apply(lambda t: t[1])


    # assemble datetime, coerce errors to NaT
    df["datetime"] = pd.to_datetime(
        dict(year=df["an"], month=df["mois"], day=df["jour"], hour=df["hour"], minute=df["minute"]),
        errors="coerce",
    )
    df["heure"] = df["datetime"].dt.hour


    df = df.rename(columns={ #on renomme
        "Num_Acc": "acc_id",
        "lat": "lat_acc",
        "long": "lon_acc"
    })


    final = df[["acc_id", "datetime", "heure", "lat_acc", "lon_acc", "dep", "com", "lum", "agg", "int", "atm", "col"]]


    OUT_C.parent.mkdir(exist_ok=True)
    final.to_csv(OUT_C, index=False)
    print(f"{len(final)} accidents géolocalisés → {OUT_C}")
    return final


if __name__ == "__main__":
    clean_caract()
