"""
app.py — Streamlit Dashboard Orchestrator
UI-only: loads data via data_loader, renders charts from charts module.
"""
from pathlib import Path

import streamlit as st
import yaml

from charts import (
    build_avg_price_chart,
    build_discount_chart,
    build_price_distribution_chart,
    build_price_vs_rating_scatter,
    build_rating_chart,
    build_top_brands_chart,
)
from data_loader import (
    build_brand_summary_table,
    calculate_kpis,
    format_summary_table,
    generate_insights,
    load_config,
    load_data,
    prepare_data,
    validate_columns,
)

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Notebooks Market Research Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Load project config ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
_config = load_config(BASE_DIR / "config" / "settings.yaml")
_dash_cfg = _config["dashboard"]

DB_PATH = BASE_DIR / _dash_cfg["db_path"]
TABLE_NAME = _dash_cfg["table_name"]


# ── Main app ─────────────────────────────────────────────────────────────────
def main() -> None:
    st.title("📊 Notebooks Market Research Dashboard")
    st.caption("Premium analytical dashboard for Mercado Livre notebook listings.")

    # ── Data loading ─────────────────────────────────────────────────────────
    try:
        df = load_data(DB_PATH, TABLE_NAME)
        validate_columns(df)
        df = prepare_data(df)
    except Exception as exc:
        st.error(f"Error loading data: {exc}")
        st.stop()

    if df.empty:
        st.warning("The dataset is empty.")
        st.stop()

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.header("Filters")

    available_brands = sorted(df["brand"].dropna().unique().tolist())
    selected_brands = st.sidebar.multiselect(
        "Select brands", options=available_brands, default=available_brands
    )

    valid_prices = df["new_money"].dropna()
    min_price = float(valid_prices.min()) if not valid_prices.empty else 0.0
    max_price = float(valid_prices.max()) if not valid_prices.empty else 10_000.0

    selected_price_range = st.sidebar.slider(
        "Price range (R$)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
    )

    top_n = st.sidebar.slider("Top N brands", min_value=5, max_value=20, value=10)

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = df.copy()
    if selected_brands:
        filtered = filtered[filtered["brand"].isin(selected_brands)]

    filtered = filtered[
        filtered["new_money"].notna()
        & filtered["new_money"].between(*selected_price_range)
    ]

    if filtered.empty:
        st.warning("No data for the selected filters.")
        st.stop()

    # ── Executive KPIs ────────────────────────────────────────────────────────
    st.subheader("💡 Executive KPIs")
    kpis = calculate_kpis(filtered)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Listings", f"{kpis['total_listings']:,}")
    c2.metric("Unique Brands", f"{kpis['unique_brands']:,}")
    c3.metric("Average Price", f"R$ {kpis['avg_price']:,.2f}")
    c4.metric("Median Price", f"R$ {kpis['median_price']:,.2f}")
    c5.metric("Average Rating", f"{kpis['avg_rating']:.2f}")
    c6.metric("Avg Discount", f"{kpis['avg_discount_pct']:.2f}%")

    # ── Automatic insights ────────────────────────────────────────────────────
    st.subheader("🧠 Automatic Insights")
    insights = generate_insights(filtered)
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Market leader (by listings):** {insights['leader_brand']}")
    c2.info(f"**Highest avg price brand:** {insights['highest_avg_price_brand']}")
    c3.info(f"**Best rated brand:** {insights['best_rated_brand']}")

    # ── Brand performance ─────────────────────────────────────────────────────
    st.subheader("📈 Brand Performance")
    fig_brands, top_brands_tbl = build_top_brands_chart(filtered, top_n)
    fig_price, avg_price_tbl = build_avg_price_chart(filtered, top_n)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_brands, use_container_width=True)
    c2.plotly_chart(fig_price, use_container_width=True)

    # ── Rating & distribution ─────────────────────────────────────────────────
    st.subheader("⭐ Rating & Price Distribution")
    fig_rating, rating_tbl = build_rating_chart(filtered, top_n)
    fig_hist = build_price_distribution_chart(filtered)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_rating, use_container_width=True)
    c2.plotly_chart(fig_hist, use_container_width=True)

    # ── Discount analysis ─────────────────────────────────────────────────────
    st.subheader("🏷️ Discount Analysis")
    fig_discount, discount_tbl = build_discount_chart(filtered, top_n)
    if fig_discount:
        st.plotly_chart(fig_discount, use_container_width=True)
    else:
        st.info("No discount data available for the current filters.")

    # ── Price vs Rating ───────────────────────────────────────────────────────
    st.subheader("🔎 Price vs Rating Relationship")
    fig_scatter = build_price_vs_rating_scatter(filtered)
    if fig_scatter:
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Not enough data to display the price vs rating chart.")

    # ── Analytical tables ─────────────────────────────────────────────────────
    st.subheader("📋 Analytical Tables")
    summary_tbl = build_brand_summary_table(filtered)
    formatted_summary = format_summary_table(summary_tbl)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Top Brands", "Average Price", "Average Rating",
        "Discount", "Brand Summary",
    ])
    with tab1:
        st.dataframe(top_brands_tbl, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(avg_price_tbl, use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(rating_tbl, use_container_width=True, hide_index=True)
    with tab4:
        st.dataframe(discount_tbl, use_container_width=True, hide_index=True)
    with tab5:
        st.dataframe(formatted_summary, use_container_width=True, hide_index=True)

    # ── Raw data expander ─────────────────────────────────────────────────────
    with st.expander("🔍 View raw dataset"):
        st.dataframe(filtered, use_container_width=True)


if __name__ == "__main__":
    main()