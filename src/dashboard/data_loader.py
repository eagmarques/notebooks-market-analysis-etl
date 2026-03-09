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

REQUIRED_COLUMNS = ["brand", "new_money", "old_money", "reviews_rating_number", "sales_bucket"]


def validate_columns(df: pd.DataFrame) -> None:
    """Raise ValueError if any required column is missing."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analytical preparation layer for the dashboard.
    Computes derived fields for marketplace analysis: price buckets, demand levels, etc.
    """
    df = df.copy()

    # 1. Basic Cleaning & Renaming
    df["price"] = pd.to_numeric(df["new_money"], errors="coerce")
    df["old_price"] = pd.to_numeric(df["old_money"], errors="coerce")
    df["rating"] = pd.to_numeric(df["reviews_rating_number"], errors="coerce").clip(0, 5)
    
    # Standardize brand (already cleaned in ETL, but defensive here)
    df["brand"] = df["brand"].fillna("Unknown").astype(str)

    # 2. Price Buckets
    def get_price_bucket(p):
        if p < 2000:
            return "Budget"
        if p < 5000:
            return "Mid-range"
        return "Premium"

    df["price_bucket"] = df["price"].apply(get_price_bucket)
    # Ensure categorical order for charts
    df["price_bucket"] = pd.Categorical(
        df["price_bucket"], categories=["Budget", "Mid-range", "Premium"], ordered=True
    )

    # 3. Demand Levels (Robust numeric mapping)
    sales_text = df["sales_bucket"].fillna("").astype(str).str.lower()
    
    # Extract numeric value
    df["sales_estimate"] = (
        sales_text
        .replace(r"^em$", "0", regex=True)
        .str.extract(r"(\d+)", expand=False)
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )
    
    # Scale "mil" values
    df.loc[sales_text.str.contains("mil|k", na=False), "sales_estimate"] *= 1000
    
    # Categorize using pd.cut
    demand_bins = [0, 100, 500, 1000, 5000, 10000, float("inf")]
    demand_labels = ["0-100", "100-500", "500-1k", "1k-5k", "5k-10k", "10k+"]
    
    df["demand_level"] = pd.cut(
        df["sales_estimate"],
        bins=demand_bins,
        labels=demand_labels,
        right=False
    )

    # 4. Discount Metrics (0-100 scale for percentage)
    df["discount_amount"] = (df["old_price"] - df["price"]).clip(lower=0)
    df["discount_pct"] = (
        (df["discount_amount"] / df["old_price"].replace(0, pd.NA) * 100)
        .fillna(0)
        .clip(0, 100)
    )

    return df


# ── KPIs ────────────────────────────────────────────────────────────────────

def calculate_kpis(df: pd.DataFrame) -> dict:
    """Compute executive KPIs over the filtered dataset."""
    valid_price = df[df["price"] > 0]
    valid_rating = df[df["rating"] > 0]
    
    return {
        "total_listings": len(df),
        "avg_price": valid_price["price"].mean() if not valid_price.empty else 0.0,
        "avg_rating": valid_rating["rating"].mean() if not valid_rating.empty else 0.0,
        "pct_discounted": (df["discount_pct"] > 0).mean() * 100,
        "high_traction_count": (df["demand_level"].isin(["500-1k", "1k-5k", "5k-10k", "10k+"])).sum(),
    }


# ── Insights ─────────────────────────────────────────────────────────────────

def generate_insights(df: pd.DataFrame) -> list[str]:
    """Generate professional market insights based on the current data slice."""
    if df.empty:
        return ["No data available for insights."]

    insights = []
    
    # Brand dominance
    brand_counts = df["brand"].value_counts()
    top_brand = brand_counts.idxmax()
    insights.append(f"**{top_brand}** dominates the current selection with {brand_counts.max()} listings.")

    # Price segment dominance
    segment_counts = df["price_bucket"].value_counts()
    top_segment = segment_counts.idxmax()
    insights.append(f"The **{top_segment}** segment is the most populated, suggesting it's the market's sweet spot.")

    # Demand levels
    demand_counts = df["demand_level"].value_counts()
    top_demand = demand_counts.idxmax()
    insights.append(f"**{top_demand}** is the most frequent demand level observed.")

    # Correlation insight (simple)
    high_rating_high_demand = df[(df["rating"] >= 4.5) & (df["demand_level"] == "High demand")]
    if len(high_rating_high_demand) > 0:
        insights.append("There is a notable cluster of **highly-rated products (4.5+)** in the **High demand** segment.")

    return insights


# ── Summary table ─────────────────────────────────────────────────────────

def build_brand_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a brand-level analytical summary table."""
    return (
        df.groupby("brand", as_index=False)
        .agg(
            total_listings=("brand", "size"),
            avg_price=("price", "mean"),
            avg_rating=("rating", "mean"),
            avg_discount=("discount_pct", "mean"),
            high_traction_share=("demand_level", lambda x: (x.isin(["500-1k", "1k-5k", "5k-10k", "10k+"])).mean() * 100)
        )
        .sort_values(["total_listings", "avg_price"], ascending=[False, False])
    )


def format_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Format numeric columns in the summary table for display."""
    formatted = df.copy()
    
    if "avg_price" in formatted.columns:
        formatted["avg_price"] = formatted["avg_price"].apply(lambda x: f"R$ {x:,.2f}")
    if "avg_rating" in formatted.columns:
        formatted["avg_rating"] = formatted["avg_rating"].apply(lambda x: f"{x:.2f}")
    if "avg_discount" in formatted.columns:
        formatted["avg_discount"] = formatted["avg_discount"].apply(lambda x: f"{x:.1f}%")
    if "high_traction_share" in formatted.columns:
        formatted["high_traction_share"] = formatted["high_traction_share"].apply(lambda x: f"{x:.1f}%")

    return formatted
