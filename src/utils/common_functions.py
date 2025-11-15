"""Shared utility helpers to reduce duplication across cleaners."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple
import re

import numpy as np
import pandas as pd


def parse_hrmn(value) -> str | float:
    """Normalize an HRMN time to 'HH:MM'. Returns np.nan if invalid.

    Handles inputs like '12:3', '1234', '7', '0730', etc.
    """
    if pd.isna(value):
        return np.nan
    s = str(value).strip()

    if ":" in s:
        parts = s.split(":")
        if len(parts) >= 2:
            hh = parts[0].zfill(2)
            mm = parts[1].zfill(2)
            return f"{hh}:{mm}"

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


def parse_position(p) -> Tuple[float | None, float | None]:
    """Extract (x, y) floats from a string; return (None, None) if unavailable."""
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


def clean_subset_csv(
    raw_path: Path,
    cleaned_path: Path,
    keep: Iterable[str],
    sep: str = ";",
) -> int:
    """Read csv, keep subset of columns present, drop rows with missing Num_Acc if present, save.

    Returns number of rows written.
    """
    df = pd.read_csv(raw_path, low_memory=False, sep=sep)

    keep_list = [c for c in keep if c in df.columns]
    if not keep_list:
        raise ValueError("None of the requested columns are present in the file.")
    df = df[keep_list].copy()

    if "Num_Acc" in df.columns:
        df = df[df["Num_Acc"].notna()]

    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cleaned_path, index=False)
    return len(df)
