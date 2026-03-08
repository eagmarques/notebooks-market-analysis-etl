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
    "rog": "Asus",
    "hp": "HP",
    "lg": "LG",
    "msi": "MSI",
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
    "compaq",
    "ultra",
    "atfly",
    "msi",
    "gigabyte",
    "toshiba",
]


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


# ── Sales bucket normalization ───────────────────────────────────────────────

SALES_BINS = [0, 100, 500, 1_000, 5_000, 10_000, float("inf")]
SALES_LABELS = ["0-100", "100-500", "500-1k", "1k-5k", "5k-10k", "10k+"]


def normalize_sales_bucket(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Convert raw sales text (e.g. '+2 mil vendidos') into:
      - sales_count_estimate: numeric estimate (int-like float)
      - sales_bucket: categorical sales range label

    Returns a tuple (sales_count_estimate, sales_bucket).
    """
    sales_text = series.fillna("").astype(str).str.lower()

    # Extract the leading number; treat sentinel "em" as 0
    raw_count = (
        sales_text
        .replace(r"^em$", "0", regex=True)
        .str.extract(r"(\d+)", expand=False)
    )
    sales_count = pd.to_numeric(raw_count, errors="coerce").fillna(0)

    # Scale up values that contain "mil" (i.e. thousands)
    is_mil = sales_text.str.contains("mil", na=False)
    sales_count = np.where(is_mil, sales_count * 1_000, sales_count)
    sales_count = pd.Series(sales_count, index=series.index, dtype="float64")

    sales_bucket = pd.cut(
        sales_count,
        bins=SALES_BINS,
        labels=SALES_LABELS,
        right=False,
    )

    return sales_count, sales_bucket
