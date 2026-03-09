"""
charts.py — Professional Plotly chart builders for marketplace analytics.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# 1️⃣ Demand Distribution
def build_demand_distribution_chart(df: pd.DataFrame):
    """Bar chart: Number of products per demand_level."""
    # Use the categorical demand_level to ensure correct ordering
    counts = df["demand_level"].value_counts().sort_index().reset_index()
    counts.columns = ["demand_level", "count"]
    
    fig = px.bar(
        counts, x="demand_level", y="count",
        title="Market Demand Distribution",
        labels={"demand_level": "Demand Segment", "count": "Product Count"},
        text_auto=True,
        color="demand_level",
        color_discrete_sequence=px.colors.sequential.PuBu_r
    )
    return fig


# 2️⃣ Price Distribution
def build_price_distribution_chart(df: pd.DataFrame):
    """Histogram of notebook prices."""
    fig = px.histogram(
        df, x="price", nbins=30,
        title="Market Price Structure",
        labels={"price": "Price (R$)", "count": "Frequency"},
        color_discrete_sequence=["#117A65"]
    )
    fig.update_layout(xaxis_title="Price (R$)", yaxis_title="Number of Listings")
    return fig


# 3️⃣ Average Price by Brand
def build_avg_price_by_brand_chart(df: pd.DataFrame, top_n: int = 15):
    """Bar chart: brand vs average price."""
    avg_prices = (
        df.groupby("brand")["price"].mean()
        .sort_values(ascending=False).head(top_n).reset_index()
    )
    fig = px.bar(
        avg_prices, x="brand", y="price",
        title=f"Brand Positioning: Average Price (Top {top_n})",
        labels={"brand": "Brand", "price": "Average Price (R$)"},
        text_auto=".2f",
        color="price",
        color_continuous_scale="Viridis"
    )
    return fig


# 4️⃣ Brand vs Demand
def build_brand_vs_demand_chart(df: pd.DataFrame, top_n: int = 10):
    """Stacked bar chart: brand vs demand_level."""
    top_brands = df["brand"].value_counts().head(top_n).index
    filtered_df = df[df["brand"].isin(top_brands)]
    
    counts = (
        filtered_df.groupby(["brand", "demand_level"], observed=True).size()
        .reset_index(name="count")
    )
    
    fig = px.bar(
        counts, x="brand", y="count", color="demand_level",
        title=f"Brand Portfolio by Demand Level (Top {top_n} Brands)",
        labels={"brand": "Brand", "count": "Listings", "demand_level": "Demand Level"},
        barmode="stack",
        color_discrete_map={
            "0-100": "#EAEDED",
            "100-500": "#D6EAF8",
            "500-1k": "#85C1E9",
            "1k-5k": "#3498DB",
            "5k-10k": "#2874A6",
            "10k+": "#1B4F72"
        }
    )
    return fig


# 5️⃣ Rating vs Demand
def build_rating_vs_demand_chart(df: pd.DataFrame):
    """Boxplot: rating vs demand_level."""
    fig = px.box(
        df, x="demand_level", y="rating",
        title="Quality Feedback vs Market Traction",
        labels={"demand_level": "Demand Segment", "rating": "Rating (0-5)"},
        points="all",
        color="demand_level",
        color_discrete_sequence=px.colors.sequential.PuBu_r
    )
    return fig


# 6️⃣ Price vs Demand
def build_price_vs_demand_chart(df: pd.DataFrame):
    """Scatter plot: x=price, y=demand_level, color=brand."""
    fig = px.strip(
        df, x="price", y="demand_level", color="brand",
        title="Price Dispersion across Demand Segments",
        labels={"price": "Price (R$)", "demand_level": "Demand Segment"},
    )
    return fig


# 7️⃣ Discount vs Demand
def build_discount_vs_demand_chart(df: pd.DataFrame):
    """Bar chart: average discount_pct per demand_level."""
    avg_discount = (
        df.groupby("demand_level", observed=True)["discount_pct"].mean()
        .reset_index()
    )
    fig = px.bar(
        avg_discount, x="demand_level", y="discount_pct",
        title="Average Discount Intensity by Demand Segment",
        labels={"demand_level": "Demand Segment", "discount_pct": "Avg Discount (%)"},
        text_auto=".1f",
        color="demand_level",
        color_discrete_sequence=px.colors.sequential.Oranges
    )
    return fig


# 8️⃣ Price Segment Analysis
def build_price_segment_chart(df: pd.DataFrame):
    """Bar chart: price_bucket vs number of products."""
    counts = df["price_bucket"].value_counts().reset_index()
    counts.columns = ["price_bucket", "count"]
    
    fig = px.bar(
        counts, x="price_bucket", y="count",
        title="Market Segmentation by Price Class",
        labels={"price_bucket": "Segment", "count": "Quantity"},
        text_auto=True,
        color="price_bucket",
        color_discrete_map={
            "Budget": "#ABEBC6",
            "Mid-range": "#58D68D",
            "Premium": "#239B56"
        }
    )
    return fig


# 9️⃣ Brand Market Share
def build_brand_market_share_chart(df: pd.DataFrame, top_n: int = 15):
    """Bar chart: brand vs product count."""
    counts = df["brand"].value_counts().head(top_n).reset_index()
    counts.columns = ["brand", "count"]
    
    fig = px.bar(
        counts, x="count", y="brand",
        orientation="h",
        title=f"Brand Inventory Share (Top {top_n})",
        labels={"brand": "Brand", "count": "Number of Listings"},
        text_auto=True,
        color="count",
        color_continuous_scale="Blues"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


# 🔟 Market Landscape Map
def build_market_landscape_chart(df: pd.DataFrame):
    """
    Scatter plot: x=price, y=rating, color=brand, size=demand_proxy.
    Visual positioning map of the market.
    """
    plot_df = df.copy()
    # Create numeric proxy for size encoding
    demand_map = {
        "0-100": 10,
        "100-500": 20,
        "500-1k": 40,
        "1k-5k": 70,
        "5k-10k": 110,
        "10k+": 160
    }
    plot_df["demand_size"] = plot_df["demand_level"].map(demand_map)
    
    fig = px.scatter(
        plot_df, x="price", y="rating", color="brand", size="demand_size",
        hover_data=["brand", "price", "rating", "demand_level"],
        title="Notebook Market Landscape: Price vs Quality vs Demand",
        labels={
            "price": "Market Price (R$)",
            "rating": "Customer Rating",
            "demand_size": "Demand Volume Proxy"
        },
        opacity=0.6
    )
    fig.update_layout(xaxis_title="Price (R$)", yaxis_title="Average Rating")
    return fig
