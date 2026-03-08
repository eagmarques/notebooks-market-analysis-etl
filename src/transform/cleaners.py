"""
cleaners.py
Funções de limpeza e conversão de campos brutos.
"""

import pandas as pd


def clean_prices(series: pd.Series) -> pd.Series:
    """
    Convert Brazilian-formatted price strings to numeric floats.

    Example: '1.234,56' → 1234.56
    """
    return (
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def clean_reviews(series: pd.Series) -> pd.Series:
    """
    Convert review rating strings to numeric floats.

    Example: '4,8 ou 5' → 4.8
    """
    return (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace("ou", "", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
    )
