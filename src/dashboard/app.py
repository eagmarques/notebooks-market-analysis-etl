import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# Page configuration
# ============================================================
st.set_page_config(
    page_title="Notebooks Market Research Dashboard",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# Constants
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "mercadolivre.db"
TABLE_NAME = "notebooks"

REQUIRED_COLUMNS = [
    "brand",
    "new_money",
    "old_money",
    "reviews_rating_number",
]


# ============================================================
# Data loading
# ============================================================
@st.cache_data(show_spinner=False)
def load_data(db_path: Path, table_name: str) -> pd.DataFrame:
    """
    Load data from the SQLite database into a pandas DataFrame.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}. "
            "Please run the ETL pipeline (python src/transformLoad/main.py) to generate it."
        )

    query = f"SELECT * FROM {table_name}"

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    return df


# ============================================================
# Data validation
# ============================================================
def validate_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    """
    Validate whether the required columns exist in the dataset.
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns in dataset: {', '.join(missing_columns)}"
        )


# ============================================================
# Data preparation
# ============================================================
def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean, standardize, and enrich the dataset for analysis.
    """
    df = df.copy()

    # Rename ambiguous scraped column to a business-friendly analytical name
    df = df.rename(columns={"reviews_rating_number": "average_rating"})

    # Standardize brand names
    df["brand"] = (
        df["brand"]
        .astype(str)
        .str.strip()
        .replace({"None": pd.NA, "nan": pd.NA, "": pd.NA})
        .fillna("Unknown")
    )

    # Convert numeric columns safely
    numeric_columns = ["new_money", "old_money", "average_rating"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep only valid rating range
    if "average_rating" in df.columns:
        df.loc[~df["average_rating"].between(0, 5), "average_rating"] = pd.NA

    # Discount calculations
    if {"old_money", "new_money"}.issubset(df.columns):
        df["discount_amount"] = df["old_money"] - df["new_money"]
        df["discount_pct"] = ((df["old_money"] - df["new_money"]) / df["old_money"]) * 100
        df.loc[df["old_money"] <= 0, "discount_pct"] = pd.NA

    return df


# ============================================================
# KPI calculations
# ============================================================
def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate high-level KPIs for the dashboard.
    """
    price_df = df[df["new_money"].notna() & (df["new_money"] > 0)]
    rating_df = df[df["average_rating"].notna() & (df["average_rating"] > 0)]

    return {
        "total_listings": len(df),
        "unique_brands": df["brand"].nunique(),
        "avg_price": price_df["new_money"].mean() if not price_df.empty else 0,
        "median_price": price_df["new_money"].median() if not price_df.empty else 0,
        "avg_rating": rating_df["average_rating"].mean() if not rating_df.empty else 0,
        "avg_discount_pct": df["discount_pct"].mean() if "discount_pct" in df.columns else 0,
    }


# ============================================================
# Insight generation
# ============================================================
def generate_insights(df: pd.DataFrame) -> dict:
    """
    Generate business insights for quick executive reading.
    """
    insights = {
        "leader_brand": "N/A",
        "highest_avg_price_brand": "N/A",
        "best_rated_brand": "N/A",
    }

    if not df.empty:
        brand_counts = df["brand"].value_counts()
        if not brand_counts.empty:
            insights["leader_brand"] = brand_counts.idxmax()

    price_df = df[df["new_money"].notna() & (df["new_money"] > 0)]
    if not price_df.empty:
        highest_avg_price = (
            price_df.groupby("brand")["new_money"]
            .mean()
            .sort_values(ascending=False)
        )
        if not highest_avg_price.empty:
            insights["highest_avg_price_brand"] = highest_avg_price.idxmax()

    rating_df = df[df["average_rating"].notna() & (df["average_rating"] > 0)]
    if not rating_df.empty:
        best_rated = (
            rating_df.groupby("brand")["average_rating"]
            .mean()
            .sort_values(ascending=False)
        )
        if not best_rated.empty:
            insights["best_rated_brand"] = best_rated.idxmax()

    return insights


# ============================================================
# Plot builders
# ============================================================
def build_top_brands_chart(df: pd.DataFrame, top_n: int):
    """
    Build a bar chart for the most frequent brands.
    """
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
    """
    Build a bar chart for average price by brand.
    """
    grouped = (
        df[df["new_money"].notna() & (df["new_money"] > 0)]
        .groupby("brand", as_index=False)
        .agg(
            avg_price=("new_money", "mean"),
            listing_count=("brand", "size"),
        )
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
    """
    Build a bar chart for average rating by brand.
    """
    grouped = (
        df[df["average_rating"].notna() & (df["average_rating"] > 0)]
        .groupby("brand", as_index=False)
        .agg(
            avg_rating=("average_rating", "mean"),
            listing_count=("brand", "size"),
        )
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
    """
    Build a histogram for notebook price distribution.
    """
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
    Build a scatter plot for price versus average rating.
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
        hover_data=[col for col in ["brand", "new_money", "average_rating"] if col in scatter_df.columns],
    )
    fig.update_layout(
        xaxis_title="Price (R$)",
        yaxis_title="Average Rating",
        showlegend=False,
    )
    return fig


def build_brand_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summarized analytical table by brand.
    """
    summary = (
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

    return summary


def format_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format the summary table for dashboard presentation.
    """
    formatted = df.copy()

    money_columns = ["avg_price", "median_price", "avg_old_price"]
    pct_columns = ["avg_discount_pct"]
    rating_columns = ["avg_rating"]

    for col in money_columns:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(
                lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "-"
            )

    for col in pct_columns:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "-"
            )

    for col in rating_columns:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(
                lambda x: f"{x:.2f}" if pd.notna(x) else "-"
            )

    return formatted


# ============================================================
# Main app
# ============================================================
def main():
    st.title("📊 Notebooks Market Research Dashboard")
    st.caption("Premium analytical dashboard for Mercado Livre notebooks listings.")

    try:
        df = load_data(DB_PATH, TABLE_NAME)
        validate_columns(df, REQUIRED_COLUMNS)
        df = prepare_data(df)
    except Exception as e:
        st.error(f"Error while loading data: {e}")
        st.stop()

    if df.empty:
        st.warning("The dataset is empty.")
        st.stop()

    # ========================================================
    # Sidebar filters
    # ========================================================
    st.sidebar.header("Filters")

    available_brands = sorted(df["brand"].dropna().unique().tolist())
    selected_brands = st.sidebar.multiselect(
        "Select brands",
        options=available_brands,
        default=available_brands,
    )

    valid_prices = df["new_money"].dropna()
    min_price = float(valid_prices.min()) if not valid_prices.empty else 0.0
    max_price = float(valid_prices.max()) if not valid_prices.empty else 10000.0

    selected_price_range = st.sidebar.slider(
        "Select price range (R$)",
        min_value=float(min_price),
        max_value=float(max_price),
        value=(float(min_price), float(max_price)),
    )

    top_n = st.sidebar.slider(
        "Top N brands",
        min_value=5,
        max_value=20,
        value=10,
    )

    filtered_df = df.copy()

    if selected_brands:
        filtered_df = filtered_df[filtered_df["brand"].isin(selected_brands)]

    filtered_df = filtered_df[
        filtered_df["new_money"].notna()
        & filtered_df["new_money"].between(selected_price_range[0], selected_price_range[1])
    ]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    # ========================================================
    # KPIs
    # ========================================================
    st.subheader("💡 Executive KPIs")

    kpis = calculate_kpis(filtered_df)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Listings", f"{kpis['total_listings']:,}")
    col2.metric("Unique Brands", f"{kpis['unique_brands']:,}")
    col3.metric("Average Price", f"R$ {kpis['avg_price']:,.2f}")
    col4.metric("Median Price", f"R$ {kpis['median_price']:,.2f}")
    col5.metric("Average Rating", f"{kpis['avg_rating']:.2f}")
    col6.metric("Average Discount", f"{kpis['avg_discount_pct']:.2f}%")

    # ========================================================
    # Automated insights
    # ========================================================
    st.subheader("🧠 Automatic Insights")

    insights = generate_insights(filtered_df)

    col1, col2, col3 = st.columns(3)
    col1.info(f"**Market leader by listing volume:** {insights['leader_brand']}")
    col2.info(f"**Highest average price brand:** {insights['highest_avg_price_brand']}")
    col3.info(f"**Best rated brand:** {insights['best_rated_brand']}")

    # ========================================================
    # Charts
    # ========================================================
    st.subheader("📈 Brand Performance")

    fig_top_brands, top_brands_table = build_top_brands_chart(filtered_df, top_n)
    fig_avg_price, avg_price_table = build_avg_price_chart(filtered_df, top_n)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_top_brands, use_container_width=True)
    with col2:
        st.plotly_chart(fig_avg_price, use_container_width=True)

    st.subheader("⭐ Rating and Distribution Analysis")

    fig_rating, rating_table = build_rating_chart(filtered_df, top_n)
    fig_price_distribution = build_price_distribution_chart(filtered_df)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_rating, use_container_width=True)
    with col2:
        st.plotly_chart(fig_price_distribution, use_container_width=True)

    st.subheader("🔎 Price vs Rating Relationship")
    fig_scatter = build_price_vs_rating_scatter(filtered_df)

    if fig_scatter is not None:
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Not enough valid data to display the price versus rating analysis.")

    # ========================================================
    # Tables
    # ========================================================
    st.subheader("📋 Analytical Tables")

    summary_table = build_brand_summary_table(filtered_df)
    formatted_summary_table = format_summary_table(summary_table)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Top Brands",
        "Average Price",
        "Average Rating",
        "Brand Summary",
    ])

    with tab1:
        st.dataframe(top_brands_table, use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(avg_price_table, use_container_width=True, hide_index=True)

    with tab3:
        st.dataframe(rating_table, use_container_width=True, hide_index=True)

    with tab4:
        st.dataframe(formatted_summary_table, use_container_width=True, hide_index=True)

    # ========================================================
    # Raw data
    # ========================================================
    with st.expander("View raw dataset"):
        st.dataframe(filtered_df, use_container_width=True)


if __name__ == "__main__":
    main()