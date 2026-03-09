"""
app.py — Streamlit Dashboard Orchestrator
UI Layer: professional marketplace insights for notebooks.
"""
from pathlib import Path
import streamlit as st

from charts import (
    build_demand_distribution_chart,
    build_price_distribution_chart,
    build_avg_price_by_brand_chart,
    build_brand_vs_demand_chart,
    build_rating_vs_demand_chart,
    build_price_vs_demand_chart,
    build_discount_vs_demand_chart,
    build_price_segment_chart,
    build_brand_market_share_chart,
    build_market_landscape_chart,
)
from data_loader import (
    load_config,
    load_data,
    validate_columns,
    prepare_data,
    calculate_kpis,
    generate_insights,
    build_brand_summary_table,
    format_summary_table,
)

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Notebook Market Intelligence",
    page_icon="💻",
    layout="wide",
)

# ── Load project config ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
_config = load_config(BASE_DIR / "config" / "settings.yaml")
_dash_cfg = _config["dashboard"]

DB_PATH = BASE_DIR / _dash_cfg["db_path"]
TABLE_NAME = _dash_cfg["table_name"]


def main() -> None:
    st.title("💻 Notebook Market Intelligence Dashboard")
    st.markdown("Professional marketplace analysis of Mercado Livre notebook listings.")

    # ── Data loading ─────────────────────────────────────────────────────────
    try:
        raw_df = load_data(DB_PATH, TABLE_NAME)
        validate_columns(raw_df)
        df = prepare_data(raw_df)
    except Exception as exc:
        st.error(f"Error loading analytical layer: {exc}")
        st.stop()

    if df.empty:
        st.warning("The analytical dataset is empty.")
        st.stop()

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.header("🔍 Market Filters")
    
    # Brand Filter
    brands = sorted(df["brand"].unique())
    selected_brands = st.sidebar.multiselect("Select Brands", options=brands, default=brands, key="filter_brands")
    
    # Price Filter
    min_p, max_p = float(df["price"].min()), float(df["price"].max())
    selected_price = st.sidebar.slider("Price Range (R$)", min_p, max_p, (min_p, max_p), key="filter_price")
    
    # Demand Level Filter
    demand_levels = df["demand_level"].cat.categories.tolist()
    selected_demand = st.sidebar.multiselect("Demand Level", options=demand_levels, default=demand_levels, key="filter_demand")
    
    # Rating Filter
    selected_rating = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 0.0, step=0.1, key="filter_rating")

    # ── Apply filters ─────────────────────────────────────────────────────────
    mask = (
        df["brand"].isin(selected_brands) &
        df["price"].between(*selected_price) &
        df["demand_level"].isin(selected_demand) &
        (df["rating"] >= selected_rating)
    )
    filtered = df[mask]

    if filtered.empty:
        st.warning("No data matches the selected filters.")
        st.stop()

    # ── EXECUTIVE KPI CARDS ───────────────────────────────────────────────────
    kpis = calculate_kpis(filtered)
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("Total Listings", f"{kpis['total_listings']:,}")
    with c2:
        st.metric("Avg Price", f"R$ {kpis['avg_price']:,.0f}")
    with c3:
        st.metric("Avg Rating", f"{kpis['avg_rating']:.2f}")
    with c4:
        st.metric("% Listings w/ Discount", f"{kpis['pct_discounted']:.1f}%")
    with c5:
        st.metric("High Traction (>500)", f"{kpis['high_traction_count']:,}")

    st.divider()

    # ── MARKET INSIGHTS ───────────────────────────────────────────────────────
    with st.expander("🧠 Key Market Insights", expanded=True):
        insights = generate_insights(filtered)
        for insight in insights:
            st.write(f"- {insight}")

    # ── ANALYTICAL VIEWS GRID ────────────────────────────────────────────────
    
    # Row 1: Demand & Price Structure
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(build_demand_distribution_chart(filtered), width="stretch")
    with c2:
        st.plotly_chart(build_price_distribution_chart(filtered), width="stretch")

    # Row 2: Brand Positioning
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(build_avg_price_by_brand_chart(filtered), width="stretch")
    with c2:
        st.plotly_chart(build_brand_market_share_chart(filtered), width="stretch")

    # Row 3: Segmentation & Portfolio
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(build_price_segment_chart(filtered), width="stretch")
    with c2:
        st.plotly_chart(build_brand_vs_demand_chart(filtered), width="stretch")

    # Row 4: Traction Performance
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(build_rating_vs_demand_chart(filtered), width="stretch")
    with c2:
        st.plotly_chart(build_discount_vs_demand_chart(filtered), width="stretch")

    # Row 5: Price vs Demand
    st.plotly_chart(build_price_vs_demand_chart(filtered), width="stretch")

    # Row 6: Landscape Map (Premium View)
    st.subheader("📍 Market Competitive Landscape")
    st.plotly_chart(build_market_landscape_chart(filtered), width="stretch")

    # ── DATA EXPLORATION ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Analytical Data Explorer")
    
    tab_summary, tab_raw = st.tabs(["Brand Summary Table", "Raw Filtered Data"])
    
    with tab_summary:
        summary_tbl = build_brand_summary_table(filtered)
        st.dataframe(format_summary_table(summary_tbl), width="stretch", hide_index=True)
        
    with tab_raw:
        st.dataframe(filtered.drop(columns=["new_money", "old_money", "reviews_rating_number"]), width="stretch")


if __name__ == "__main__":
    main()