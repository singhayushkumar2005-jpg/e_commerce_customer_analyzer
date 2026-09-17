"""
app.py
------
E-Commerce Sales & Customer Analytics Dashboard (Streamlit entry point).

Run with:
    streamlit run src/app.py
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing import load_and_prepare_data
import analytics as an
import visualization as viz

# --------------------------------------------------------------------------
# Page config & styling
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEMES = {
    "Light": {
        "page": "#F3F7F5", "surface": "#FFFFFF", "surface_alt": "#E6F0ED",
        "border": "#D5E3DF", "text": "#17343A", "muted": "#607477",
        "sidebar": "#123B40", "sidebar_text": "#F2FBF8",
        "accent": "#0D9488",
        "shadow": "rgba(31, 41, 55, 0.08)",
    },
    "Dark": {
        "page": "#0D1E21", "surface": "#153035", "surface_alt": "#204349",
        "border": "#31565A", "text": "#ECF8F5", "muted": "#A9C3C1",
        "sidebar": "#091719", "sidebar_text": "#ECF8F5",
        "accent": "#2DD4BF",
        "shadow": "rgba(0, 0, 0, 0.22)",
    },
}

if "theme" not in st.session_state:
    st.session_state.theme = "Light"

theme_name = st.sidebar.radio(
    "Appearance", ["Light", "Dark"], horizontal=True,
    index=["Light", "Dark"].index(st.session_state.theme), key="theme",
)
theme = THEMES[theme_name]
viz.set_theme(theme_name)

CUSTOM_CSS = f"""
<style>
    :root {{ color-scheme: {theme_name.lower()}; --page: {theme['page']}; --accent: {theme['accent']};
        --surface: {theme['surface']}; --surface-alt: {theme['surface_alt']};
        --border: {theme['border']}; --text: {theme['text']}; --muted: {theme['muted']}; }}
    .stApp, [data-testid="stAppViewContainer"] {{ background-color: var(--page); color: var(--text); }}
    .main {{ background-color: var(--page); }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    div[data-testid="stMetric"] {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px 10px 18px;
        box-shadow: 0 1px 3px {theme['shadow']};
    }}
    div[data-testid="stMetricLabel"] {{ font-size: 13px; color: var(--muted); font-weight: 500; }}
    div[data-testid="stMetricValue"] {{ font-size: 26px; color: var(--text); font-weight: 700; }}

    section[data-testid="stSidebar"] {{
        background-color: {theme['sidebar']};
    }}
    section[data-testid="stSidebar"] * {{ color: {theme['sidebar_text']} !important; }}
    [data-baseweb="tag"], [data-testid="stMultiSelect"] span[data-tag] {{
        background-color: var(--accent) !important;
    }}
    input[type="radio"] {{ accent-color: var(--accent); }}
    label[data-testid="stRadioOption"][data-selected="true"] > div > div > div:first-child > div:first-child {{
        background-color: var(--accent) !important; border-color: var(--accent) !important;
    }}
    button[role="tab"][aria-selected="true"] {{
        color: var(--accent) !important; border-bottom-color: var(--accent) !important;
    }}

    h1, h2, h3 {{ color: var(--text); font-family: 'Inter', 'Segoe UI', sans-serif; }}
    p, label, [data-testid="stCaptionContainer"] {{ color: var(--muted); }}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div,
    div[data-testid="stDataFrame"] {{ background: var(--surface); border-color: var(--border); }}
    div[data-testid="stExpander"] {{ border-color: var(--border); background: var(--surface); }}
    .block-container {{ padding-top: 1.5rem; }}

    .badge {{
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 600; margin-right: 6px;
    }}
    .badge-purple {{ background: #DDF5F0; color: #0F766E; }}
    .badge-green {{ background: #DDF5F0; color: #0F766E; }}
    .badge-red {{ background: #FDE3DE; color: #C24132; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Data loading (cached)
# --------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading and preparing e-commerce data...")
def get_data():
    full_df, customers, products = load_and_prepare_data()
    return full_df, customers, products


full_df, customers_df, products_df = get_data()


# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------

st.sidebar.markdown("## 🛍️ Filters")
st.sidebar.caption("Refine the dashboard using the controls below.")

min_date = full_df["order_date"].min().date()
max_date = full_df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

categories = sorted(full_df["category"].unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

regions = sorted(full_df["region"].unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

statuses = sorted(full_df["order_status"].unique())
selected_statuses = st.sidebar.multiselect("Order status", statuses, default=statuses)

cust_types = sorted(full_df["customer_type"].unique())
selected_cust_types = st.sidebar.multiselect("Customer type", cust_types, default=cust_types)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Dataset: **{full_df['order_id'].nunique():,}** orders · "
    f"**{full_df['customer_id'].nunique():,}** customers · "
    f"**{products_df.shape[0]:,}** products"
)
st.sidebar.caption("Built with Python · Pandas · NumPy · Plotly · Streamlit")

# Apply filters
mask = (
    (full_df["order_date"].dt.date >= start_date)
    & (full_df["order_date"].dt.date <= end_date)
    & (full_df["category"].isin(selected_categories))
    & (full_df["region"].isin(selected_regions))
    & (full_df["order_status"].isin(selected_statuses))
    & (full_df["customer_type"].isin(selected_cust_types))
)
fdf = full_df[mask].copy()

if fdf.empty:
    st.warning("No data matches the selected filters. Please broaden your filter selection.")
    st.stop()


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.markdown("# 🛍️ E-Commerce Sales & Customer Analytics Dashboard")
st.caption(
    f"Analyzing orders from **{start_date}** to **{end_date}** · "
    f"{len(selected_categories)} categories · {len(selected_regions)} regions"
)

# --------------------------------------------------------------------------
# KPI Row
# --------------------------------------------------------------------------

kpis = an.compute_kpis(fdf)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Total Revenue", f"${kpis['total_revenue']:,.0f}")
k2.metric("📈 Total Profit", f"${kpis['total_profit']:,.0f}", f"{kpis['profit_margin_pct']:.1f}% margin")
k3.metric("📦 Total Orders", f"{kpis['total_orders']:,}")
k4.metric("🧾 Avg Order Value", f"${kpis['avg_order_value']:,.2f}")
k5.metric("↩️ Cancel/Return Rate", f"{kpis['cancellation_return_rate_pct']:.1f}%")

st.markdown("")

# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------

tab_overview, tab_products, tab_customers, tab_rfm, tab_anomaly, tab_behavior = st.tabs(
    ["📊 Overview", "🏆 Products", "👥 Customers", "🎯 RFM Segmentation", "🚨 Anomaly Detection", "🔎 Purchase Behavior"]
)

# ---------------- Overview ----------------
with tab_overview:
    trend_granularity = st.radio("Trend granularity", ["Monthly", "Weekly"], horizontal=True, key="trend_gran")

    if trend_granularity == "Monthly":
        trend = an.monthly_trend(fdf)
        x_col = "order_year_month"
    else:
        trend = an.weekly_trend(fdf)
        x_col = "order_week"

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(viz.revenue_trend_chart(trend, x_col), use_container_width=True)
    with c2:
        st.plotly_chart(viz.orders_trend_chart(trend, x_col), use_container_width=True)

    c3, c4 = st.columns(2)
    cat_df = an.category_sales(fdf)
    with c3:
        st.plotly_chart(viz.category_bar_chart(cat_df), use_container_width=True)
    with c4:
        region_df = an.sales_by_region(fdf)
        st.plotly_chart(viz.region_bar_chart(region_df), use_container_width=True)

    st.plotly_chart(viz.subcategory_treemap(cat_df), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        country_df = an.sales_by_country(fdf)
        st.plotly_chart(viz.country_choropleth(country_df), use_container_width=True)
    with c6:
        status_df = an.order_status_breakdown(fdf)
        st.plotly_chart(viz.order_status_donut(status_df), use_container_width=True)

# ---------------- Products ----------------
with tab_products:
    st.markdown("### Top 10 Products")
    metric_choice = st.radio(
        "Rank by", ["Revenue (best-selling)", "Profit (most profitable)", "Units sold"],
        horizontal=True, key="top_products_metric"
    )
    by_map = {"Revenue (best-selling)": "net_sales", "Profit (most profitable)": "profit", "Units sold": "quantity"}
    val_col_map = {"net_sales": "revenue", "profit": "profit", "quantity": "units"}
    by = by_map[metric_choice]
    top10 = an.top_products(fdf, n=10, by=by)

    st.plotly_chart(
        viz.top_products_bar(top10, val_col_map[by], metric_choice, f"Top 10 Products by {metric_choice}"),
        use_container_width=True
    )

    with st.expander("View full top-10 table"):
        display_df = top10.copy()
        display_df["revenue"] = display_df["revenue"].map("${:,.2f}".format)
        display_df["profit"] = display_df["profit"].map("${:,.2f}".format)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("### Category & Sub-Category Performance")
    cat_df_full = an.category_sales(fdf)
    display_cat = cat_df_full.copy()
    display_cat["revenue"] = display_cat["revenue"].map("${:,.2f}".format)
    display_cat["profit"] = display_cat["profit"].map("${:,.2f}".format)
    st.dataframe(display_cat, use_container_width=True, hide_index=True, height=350)

# ---------------- Customers ----------------
with tab_customers:
    c1, c2 = st.columns(2)
    with c1:
        nvr_df = an.new_vs_returning(fdf)
        st.plotly_chart(viz.new_vs_returning_donut(nvr_df), use_container_width=True)
    with c2:
        seg_df = an.customer_spending_segments(fdf)
        seg_summary = seg_df.groupby("spend_segment", observed=True).agg(
            customers=("customer_id", "nunique")
        ).reset_index()
        st.plotly_chart(viz.spend_segment_bar(seg_summary), use_container_width=True)

    st.markdown("### Spending Segment Detail")
    seg_detail = seg_df.groupby("spend_segment", observed=True).agg(
        customers=("customer_id", "nunique"),
        avg_total_spend=("total_spend", "mean"),
        avg_orders=("orders", "mean"),
        avg_order_value=("avg_order_value", "mean"),
    ).reset_index()
    seg_detail["avg_total_spend"] = seg_detail["avg_total_spend"].map("${:,.2f}".format)
    seg_detail["avg_order_value"] = seg_detail["avg_order_value"].map("${:,.2f}".format)
    seg_detail["avg_orders"] = seg_detail["avg_orders"].round(1)
    st.dataframe(seg_detail, use_container_width=True, hide_index=True)

    st.markdown("### Payment & Shipping Preferences")
    payment_df, shipping_df = an.preferred_payment_and_shipping(fdf)
    p1, p2 = st.columns(2)
    fig_pay, fig_ship = viz.payment_shipping_charts(payment_df, shipping_df)
    with p1:
        st.plotly_chart(fig_pay, use_container_width=True)
    with p2:
        st.plotly_chart(fig_ship, use_container_width=True)

# ---------------- RFM Segmentation ----------------
with tab_rfm:
    st.markdown(
        "**RFM analysis** scores every customer on **R**ecency (days since last order), "
        "**F**requency (number of orders), and **M**onetary value (total spend), each on a 1–5 scale, "
        "then groups customers into actionable segments."
    )
    rfm_df = an.compute_rfm(fdf)
    rfm_summary = an.rfm_segment_summary(rfm_df)

    st.plotly_chart(viz.rfm_segment_bar(rfm_summary), use_container_width=True)
    st.plotly_chart(viz.rfm_scatter(rfm_df), use_container_width=True)

    with st.expander("View RFM segment summary table"):
        display_rfm = rfm_summary.copy()
        display_rfm["avg_recency_days"] = display_rfm["avg_recency_days"].round(1)
        display_rfm["avg_frequency"] = display_rfm["avg_frequency"].round(2)
        display_rfm["avg_monetary"] = display_rfm["avg_monetary"].map("${:,.2f}".format)
        display_rfm["total_monetary"] = display_rfm["total_monetary"].map("${:,.2f}".format)
        st.dataframe(display_rfm, use_container_width=True, hide_index=True)

    with st.expander("View individual customer RFM scores"):
        st.dataframe(
            rfm_df[["customer_id", "recency", "frequency", "monetary", "R_score", "F_score", "M_score",
                    "RFM_score", "segment"]].sort_values("monetary", ascending=False),
            use_container_width=True, hide_index=True, height=350
        )

# ---------------- Anomaly Detection ----------------
with tab_anomaly:
    st.markdown(
        "Anomalies are flagged using a **rolling z-score**: each day's revenue is compared to a "
        "local rolling average and standard deviation, so genuine spikes/drops are detected even "
        "as the underlying trend shifts over time."
    )
    col_a, col_b = st.columns([1, 3])
    with col_a:
        z_thresh = st.slider("Sensitivity (z-score threshold)", 1.0, 4.0, 2.0, 0.25,
                              help="Lower = more sensitive (flags more points)")
        window = st.slider("Rolling window (days)", 3, 21, 7, 2)

    daily = an.daily_trend(fdf)
    anomaly_df = an.detect_sales_anomalies(daily, value_col="revenue", z_thresh=z_thresh, window=window)

    st.plotly_chart(viz.anomaly_chart(anomaly_df, "date", "revenue"), use_container_width=True)

    n_spikes = (anomaly_df.get("anomaly_type") == "Spike").sum()
    n_drops = (anomaly_df.get("anomaly_type") == "Drop").sum()
    b1, b2 = st.columns(2)
    b1.markdown(f"<span class='badge badge-green'>▲ {n_spikes} spike days</span>", unsafe_allow_html=True)
    b2.markdown(f"<span class='badge badge-red'>▼ {n_drops} drop days</span>", unsafe_allow_html=True)

    with st.expander("View flagged anomaly days"):
        flagged = anomaly_df[anomaly_df["is_anomaly"]].sort_values("date", ascending=False)
        display_flag = flagged[["date", "revenue", "rolling_mean", "z_score", "anomaly_type"]].copy()
        display_flag["revenue"] = display_flag["revenue"].map("${:,.2f}".format)
        display_flag["rolling_mean"] = display_flag["rolling_mean"].map("${:,.2f}".format)
        display_flag["z_score"] = display_flag["z_score"].round(2)
        st.dataframe(display_flag, use_container_width=True, hide_index=True)

# ---------------- Purchase Behavior ----------------
with tab_behavior:
    behavior = an.purchase_behavior_summary(fdf)
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Avg Orders / Customer", f"{behavior['avg_orders_per_customer']:.2f}")
    b2.metric("Median Orders / Customer", f"{behavior['median_orders_per_customer']:.0f}")
    b3.metric("Avg Items / Order", f"{behavior['avg_items_per_order']:.2f}")
    b4.metric("Repeat Purchase Rate", f"{behavior['repeat_purchase_rate_pct']:.1f}%")

    st.markdown("### Order Status Detail")
    status_df = an.order_status_breakdown(fdf)
    display_status = status_df.copy()
    display_status["pct"] = display_status["pct"].map("{:.1f}%".format)
    st.dataframe(display_status, use_container_width=True, hide_index=True)

    st.markdown("### Revenue & Profit by Region (Detail)")
    region_df = an.sales_by_region(fdf)
    display_region = region_df.copy()
    display_region["revenue"] = display_region["revenue"].map("${:,.2f}".format)
    display_region["profit"] = display_region["profit"].map("${:,.2f}".format)
    st.dataframe(display_region, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("E-Commerce Sales & Customer Analytics Dashboard · Synthetic dataset generated for demonstration purposes.")
