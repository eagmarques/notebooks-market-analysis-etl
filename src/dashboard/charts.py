"""
charts.py — Plotly chart builders for the dashboard.
Each function receives a filtered DataFrame and returns a Plotly Figure.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px


def build_top_brands_chart(df: pd.DataFrame, top_n: int):
    """Bar chart: most frequent brands by listing count."""
    brand_counts = df["brand"].value_counts().head(top_n).reset_index()
    brand_counts.columns = ["brand", "count"]

    fig = px.bar(
        brand_counts,
        x="brand",
        y="count",
        title=f"Top {top_n} Brands by Number of Listings",
        text_auto=True,
    )
    fig.update_layout(xaxis_title="Brand", yaxis_title="Listings")
    return fig, brand_counts


def build_avg_price_chart(df: pd.DataFrame, top_n: int):
    """Bar chart: average current price by brand."""
    grouped = (
        df[df["new_money"].notna() & (df["new_money"] > 0)]
        .groupby("brand", as_index=False)
        .agg(avg_price=("new_money", "mean"), listing_count=("brand", "size"))
        .sort_values("avg_price", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        grouped,
        x="brand",
        y="avg_price",
        title=f"Top {top_n} Brands by Average Price",
        text_auto=".2f",
        hover_data=["listing_count"],
    )
    fig.update_layout(xaxis_title="Brand", yaxis_title="Average Price (R$)")
    return fig, grouped


def build_rating_chart(df: pd.DataFrame, top_n: int):
    """Bar chart: average rating by brand."""
    grouped = (
        df[df["average_rating"].notna() & (df["average_rating"] > 0)]
        .groupby("brand", as_index=False)
        .agg(avg_rating=("average_rating", "mean"), listing_count=("brand", "size"))
        .sort_values("avg_rating", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        grouped,
        x="brand",
        y="avg_rating",
        title=f"Top {top_n} Brands by Average Rating",
        text_auto=".2f",
        hover_data=["listing_count"],
    )
    fig.update_layout(xaxis_title="Brand", yaxis_title="Average Rating")
    return fig, grouped


def build_price_distribution_chart(df: pd.DataFrame):
    """Histogram: distribution of notebook prices."""
    valid_df = df[df["new_money"].notna() & (df["new_money"] > 0)]

    fig = px.histogram(
        valid_df,
        x="new_money",
        nbins=30,
        title="Price Distribution",
    )
    fig.update_layout(xaxis_title="Price (R$)", yaxis_title="Frequency")
    return fig


def build_price_vs_rating_scatter(df: pd.DataFrame):
    """
    Scatter plot: price versus average rating coloured by brand.
    Returns None if there is not enough valid data.
    """
    scatter_df = df[
        df["new_money"].notna()
        & (df["new_money"] > 0)
        & df["average_rating"].notna()
        & (df["average_rating"] > 0)
    ].copy()

    if scatter_df.empty:
        return None

    fig = px.scatter(
        scatter_df,
        x="new_money",
        y="average_rating",
        color="brand",
        title="Price vs Average Rating",
        hover_data=["brand", "new_money", "average_rating"],
    )
    fig.update_layout(
        xaxis_title="Price (R$)",
        yaxis_title="Average Rating",
        showlegend=False,
    )
    return fig


def build_discount_chart(df: pd.DataFrame, top_n: int):
    """Bar chart: average discount percentage by brand."""
    grouped = (
        df[df["discount_pct"].notna() & (df["discount_pct"] > 0)]
        .groupby("brand", as_index=False)
        .agg(avg_discount=("discount_pct", "mean"), listing_count=("brand", "size"))
        .sort_values("avg_discount", ascending=False)
        .head(top_n)
    )

    if grouped.empty:
        return None, grouped

    fig = px.bar(
        grouped,
        x="brand",
        y="avg_discount",
        title=f"Top {top_n} Brands by Average Discount (%)",
        text_auto=".1f",
        hover_data=["listing_count"],
    )
    fig.update_layout(xaxis_title="Brand", yaxis_title="Avg Discount (%)")
    return fig, grouped
