"""
data_loader.py — Dashboard data access and preparation layer.
All data logic lives here; app.py is responsible only for UI.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml


# ── Config ─────────────────────────────────────────────────────────────────

def load_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Database access ─────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_data(db_path: Path, table_name: str) -> pd.DataFrame:
    """
    Load data from the SQLite database into a pandas DataFrame.
    Results are cached by Streamlit until the DB file changes.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}. "
            "Run the ETL first: python src/transform/main.py"
        )
    query = f"SELECT * FROM {table_name}"  # noqa: S608 (table_name is config-defined)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn)


# ── Validation ──────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = ["brand", "new_money", "old_money", "reviews_rating_number"]


def validate_columns(df: pd.DataFrame) -> None:
    """Raise ValueError if any required column is missing."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


# ── Data preparation ────────────────────────────────────────────────────────

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Light preparation layer for the dashboard.
    Heavy cleaning (price parsing, brand inference) is the ETL's responsibility.
    Here we only: rename columns, guard against bad values, and compute discounts.
    """
    df = df.copy()

    # Rename to a business-friendly analytical name
    df = df.rename(columns={"reviews_rating_number": "average_rating"})

    # Guard against residual NaN-like strings from older ETL runs
    df["brand"] = (
        df["brand"]
        .astype(str)
        .str.strip()
        .replace({"None": pd.NA, "nan": pd.NA, "": pd.NA})
        .fillna("Unknown")
    )

    # Ensure numeric types (data stored in SQLite can come back as object)
    for col in ["new_money", "old_money", "average_rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Sanitize ratings: keep only [0, 5]
    if "average_rating" in df.columns:
        df.loc[~df["average_rating"].between(0, 5), "average_rating"] = pd.NA

    # Derived discount metrics
    if {"old_money", "new_money"}.issubset(df.columns):
        df["discount_amount"] = df["old_money"] - df["new_money"]
        valid_old = df["old_money"].gt(0)
        df["discount_pct"] = (
            df["discount_amount"].where(valid_old) / df["old_money"].where(valid_old) * 100
        )
        # SANITY GUARD: Discount must be within [0, 100]
        if "discount_pct" in df.columns:
            df["discount_pct"] = df["discount_pct"].clip(0, 100)

    return df


# ── KPIs ────────────────────────────────────────────────────────────────────

def calculate_kpis(df: pd.DataFrame) -> dict:
    """Compute executive KPIs over the filtered dataset."""
    price_df = df[df["new_money"].notna() & (df["new_money"] > 0)]
    rating_df = df[df["average_rating"].notna() & (df["average_rating"] > 0)]

    return {
        "total_listings": len(df),
        "unique_brands": df["brand"].nunique(),
        "avg_price": price_df["new_money"].mean() if not price_df.empty else 0.0,
        "median_price": price_df["new_money"].median() if not price_df.empty else 0.0,
        "avg_rating": rating_df["average_rating"].mean() if not rating_df.empty else 0.0,
        "avg_discount_pct": df["discount_pct"].mean() if "discount_pct" in df.columns else 0.0,
    }


# ── Insights ─────────────────────────────────────────────────────────────────

def generate_insights(df: pd.DataFrame) -> dict:
    """Generate quick business insights for executive reading."""
    insights = {
        "leader_brand": "N/A",
        "highest_avg_price_brand": "N/A",
        "best_rated_brand": "N/A",
    }

    if df.empty:
        return insights

    brand_counts = df["brand"].value_counts()
    if not brand_counts.empty:
        insights["leader_brand"] = brand_counts.idxmax()

    price_df = df[df["new_money"].notna() & (df["new_money"] > 0)]
    if not price_df.empty:
        insights["highest_avg_price_brand"] = (
            price_df.groupby("brand")["new_money"].mean().idxmax()
        )

    rating_df = df[df["average_rating"].notna() & (df["average_rating"] > 0)]
    if not rating_df.empty:
        insights["best_rated_brand"] = (
            rating_df.groupby("brand")["average_rating"].mean().idxmax()
        )

    return insights


# ── Summary table ─────────────────────────────────────────────────────────

def build_brand_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a brand-level analytical summary table."""
    return (
        df.groupby("brand", as_index=False)
        .agg(
            total_listings=("brand", "size"),
            avg_price=("new_money", "mean"),
            median_price=("new_money", "median"),
            avg_old_price=("old_money", "mean"),
            avg_rating=("average_rating", "mean"),
            avg_discount_pct=("discount_pct", "mean"),
        )
        .sort_values(["total_listings", "avg_price"], ascending=[False, False])
    )


def format_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Format numeric columns in the summary table for display."""
    formatted = df.copy()

    def fmt_money(x):
        return f"R$ {x:,.2f}" if pd.notna(x) else "-"

    def fmt_pct(x):
        return f"{x:.2f}%" if pd.notna(x) else "-"

    def fmt_rating(x):
        return f"{x:.2f}" if pd.notna(x) else "-"

    for col in ["avg_price", "median_price", "avg_old_price"]:
        if col in formatted.columns:
            formatted[col] = formatted[col].apply(fmt_money)

    if "avg_discount_pct" in formatted.columns:
        formatted["avg_discount_pct"] = formatted["avg_discount_pct"].apply(fmt_pct)

    if "avg_rating" in formatted.columns:
        formatted["avg_rating"] = formatted["avg_rating"].apply(fmt_rating)

    return formatted
