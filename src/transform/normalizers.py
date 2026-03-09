"""
normalizers.py
Funções de normalização de campos de negócio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ── Brand normalization ──────────────────────────────────────────────────────

# Order matters: longer/more-specific aliases must come before shorter ones.
BRAND_ALIASES: dict[str, str] = {
    "galaxy book": "Samsung",
    "macbook": "Apple",
    "legion": "Lenovo",
    "ideapad": "Lenovo",
    "thinkpad": "Lenovo",
    "yoga": "Lenovo",
    "rog": "Asus",
    "hp": "HP",
    "compaq": "HP",
    "lg": "LG",
    "msi": "MSI",
    "chromebook": "Acer",
    "aspire": "Acer",
    "nitro": "Acer",
    "predator": "Acer",
    "swift": "Acer",
    "alienware": "Dell",
    "ultra": "Multilaser",
}

# Ordered by priority (more specific first when aliases overlap).
KNOWN_BRANDS: list[str] = [
    "galaxy book",
    "macbook",
    "legion",
    "rog",
    "dell",
    "hp",
    "lenovo",
    "acer",
    "apple",
    "asus",
    "samsung",
    "positivo",
    "vaio",
    "multilaser",
    "lg",
    "atfly",
    "msi",
    "gigabyte",
    "toshiba",
    "realme",
    "xiaomi",
    "redmi",
    "huawei",
    "chuwi",
    "teclast",
    "concórdia",
    "concórdia",
    "philco",
]

# Canonical brands returned by normalize_brand
CANONICAL_BRANDS: set[str] = {
    BRAND_ALIASES.get(b, b.capitalize()) for b in KNOWN_BRANDS
}


def normalize_brand(title: str | None) -> str | None:
    """
    Infer notebook brand from product title using keyword matching.

    Returns the canonical brand name or None if no match is found.
    """
    if not title:
        return None

    title_lower = title.lower()
    for brand in KNOWN_BRANDS:
        if brand in title_lower:
            return BRAND_ALIASES.get(brand, brand.capitalize())

    return None


def normalize_brand_series(series: pd.Series) -> pd.Series:
    """Vectorised wrapper of normalize_brand for a Pandas Series."""
    return series.map(normalize_brand)


