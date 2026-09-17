"""
visualization.py
-----------------
Reusable Plotly chart builders for the Streamlit dashboard. Keeping chart
construction here keeps app.py focused on layout/interaction.
"""

import plotly.express as px
import plotly.graph_objects as go

# Consistent color palette across the dashboard
PALETTE = ["#0D9488", "#F59E0B", "#F26B5E", "#3B82A0", "#7C9A92", "#D97706"]
ACCENT = "#0D9488"
POSITIVE = "#0F9D78"
NEGATIVE = "#D9574C"
NEUTRAL = "#6B8585"

THEME_LAYOUTS = {
    "Light": {"template": "plotly_white", "font_color": "#2D3436", "hover_bgcolor": "white"},
    "Dark": {"template": "plotly_dark", "font_color": "#F4F7FC", "hover_bgcolor": "#182033"},
}
CURRENT_THEME = "Light"


def set_theme(theme_name):
    """Set chart defaults to match the dashboard appearance."""
    global CURRENT_THEME, PALETTE, ACCENT, POSITIVE, NEGATIVE, NEUTRAL
    CURRENT_THEME = theme_name
    if theme_name == "Dark":
        PALETTE = ["#2DD4BF", "#FBBF24", "#FB8072", "#66B3CC", "#9CC9BD", "#F59E0B"]
        ACCENT, POSITIVE, NEGATIVE, NEUTRAL = "#2DD4BF", "#34D399", "#FB8072", "#9BB8B7"
    else:
        PALETTE = ["#0D9488", "#F59E0B", "#F26B5E", "#3B82A0", "#7C9A92", "#D97706"]
        ACCENT, POSITIVE, NEGATIVE, NEUTRAL = "#0D9488", "#0F9D78", "#D9574C", "#6B8585"


def _base_layout():
    theme = THEME_LAYOUTS[CURRENT_THEME]
    return dict(
        template=theme["template"],
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color=theme["font_color"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor=theme["hover_bgcolor"], font_size=12),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

BASE_LAYOUT = dict(
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def _apply_base(fig, title=None, height=380):
    fig.update_layout(**_base_layout())
    if title:
        fig.update_layout(title=dict(text=title, x=0, font=dict(size=16)))
    fig.update_layout(height=height)
    return fig


def revenue_trend_chart(trend_df, x_col, title="Revenue & Profit Trend"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_df[x_col], y=trend_df["revenue"], mode="lines+markers", name="Revenue",
        line=dict(color=ACCENT, width=3), fill="tozeroy", fillcolor="rgba(13,148,136,0.12)"
    ))
    fig.add_trace(go.Scatter(
        x=trend_df[x_col], y=trend_df["profit"], mode="lines+markers", name="Profit",
        line=dict(color=POSITIVE, width=2, dash="dot")
    ))
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Amount ($)")
    return _apply_base(fig, title)


def orders_trend_chart(trend_df, x_col, title="Orders & Avg Order Value"):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=trend_df[x_col], y=trend_df["orders"], name="Orders",
                          marker_color=ACCENT, opacity=0.75, yaxis="y"))
    fig.add_trace(go.Scatter(x=trend_df[x_col], y=trend_df.get("avg_order_value", trend_df.get("revenue")),
                              name="Avg Order Value", mode="lines+markers",
                              line=dict(color="#E17055", width=2), yaxis="y2"))
    fig.update_layout(
        yaxis=dict(title="Orders"),
        yaxis2=dict(title="AOV ($)", overlaying="y", side="right", showgrid=False),
    )
    return _apply_base(fig, title)


def category_bar_chart(cat_df, title="Sales by Category"):
    grouped = cat_df.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue")
    fig = px.bar(grouped, x="revenue", y="category", orientation="h",
                 color="revenue", color_continuous_scale="Tealgrn", text_auto=".2s")
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(title="Revenue ($)")
    fig.update_yaxes(title=None)
    return _apply_base(fig, title)


def subcategory_treemap(cat_df, title="Category → Sub-Category Revenue Breakdown"):
    fig = px.treemap(
        cat_df, path=["category", "sub_category"], values="revenue",
        color="profit", color_continuous_scale="RdYlGn",
        hover_data={"revenue": ":.2f", "profit": ":.2f"}
    )
    fig.update_traces(textinfo="label+value")
    return _apply_base(fig, title, height=450)


def top_products_bar(prod_df, value_col, label, title):
    fig = px.bar(
        prod_df.sort_values(value_col), x=value_col, y="product_name", orientation="h",
        color=value_col, color_continuous_scale="Teal", text_auto=".2s",
        hover_data=["category", "sub_category"]
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(title=label)
    fig.update_yaxes(title=None)
    return _apply_base(fig, title, height=420)


def region_bar_chart(region_df, title="Revenue by Region"):
    fig = px.bar(
        region_df.sort_values("revenue"), x="revenue", y="region", orientation="h",
        color="revenue", color_continuous_scale="Blues", text_auto=".2s"
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(title="Revenue ($)")
    fig.update_yaxes(title=None)
    return _apply_base(fig, title)


def country_choropleth(country_df, title="Revenue by Country"):
    fig = px.choropleth(
        country_df, locations="country", locationmode="country names",
        color="revenue", color_continuous_scale="Tealgrn",
        hover_data=["orders", "profit"]
    )
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth")
    return _apply_base(fig, title, height=420)


def order_status_donut(status_df, title="Order Status Breakdown"):
    fig = px.pie(
        status_df, names="order_status", values="orders", hole=0.55,
        color_discrete_sequence=PALETTE
    )
    fig.update_traces(textinfo="percent+label")
    return _apply_base(fig, title, height=360)


def new_vs_returning_donut(nvr_df, title="New vs Returning Customers"):
    fig = px.pie(
        nvr_df, names="customer_type", values="orders", hole=0.55,
        color="customer_type",
        color_discrete_map={"New": "#F59E0B", "Returning": "#0D9488"}
    )
    fig.update_traces(textinfo="percent+label")
    return _apply_base(fig, title, height=360)


def spend_segment_bar(seg_summary_df, title="Customers by Spending Segment"):
    fig = px.bar(
        seg_summary_df, x="spend_segment", y="customers", color="spend_segment",
        color_discrete_sequence=PALETTE, text_auto=True
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Customers")
    return _apply_base(fig, title, height=360)


def rfm_segment_bar(rfm_summary_df, title="RFM Customer Segments"):
    fig = px.bar(
        rfm_summary_df.sort_values("total_monetary"), x="total_monetary", y="segment", orientation="h",
        color="segment", color_discrete_sequence=PALETTE,
        text=rfm_summary_df.sort_values("total_monetary")["customers"].astype(str) + " customers"
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title="Total Revenue ($)")
    fig.update_yaxes(title=None)
    return _apply_base(fig, title, height=420)


def rfm_scatter(rfm_df, title="RFM Scatter: Recency vs Frequency (bubble = Monetary)"):
    fig = px.scatter(
        rfm_df, x="recency", y="frequency", size="monetary", color="segment",
        color_discrete_sequence=PALETTE, hover_data=["customer_id", "monetary"],
        size_max=40, opacity=0.75
    )
    fig.update_xaxes(title="Recency (days since last purchase)")
    fig.update_yaxes(title="Frequency (orders)")
    return _apply_base(fig, title, height=450)


def anomaly_chart(anomaly_df, x_col, value_col="revenue", title="Sales Anomaly Detection"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anomaly_df[x_col], y=anomaly_df[value_col], mode="lines", name=value_col.title(),
        line=dict(color=ACCENT, width=2)
    ))
    fig.add_trace(go.Scatter(
        x=anomaly_df[x_col], y=anomaly_df["rolling_mean"], mode="lines", name="Expected (rolling avg)",
        line=dict(color=NEUTRAL, width=1, dash="dot")
    ))

    if "anomaly_type" in anomaly_df.columns:
        spikes = anomaly_df[anomaly_df["anomaly_type"] == "Spike"]
        drops = anomaly_df[anomaly_df["anomaly_type"] == "Drop"]
    else:
        spikes = anomaly_df.iloc[0:0]
        drops = anomaly_df.iloc[0:0]
    if len(spikes):
        fig.add_trace(go.Scatter(
            x=spikes[x_col], y=spikes[value_col], mode="markers", name="Spike",
            marker=dict(color=POSITIVE, size=11, symbol="triangle-up", line=dict(width=1, color="white"))
        ))
    if len(drops):
        fig.add_trace(go.Scatter(
            x=drops[x_col], y=drops[value_col], mode="markers", name="Drop",
            marker=dict(color=NEGATIVE, size=11, symbol="triangle-down", line=dict(width=1, color="white"))
        ))
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=value_col.title() + " ($)")
    return _apply_base(fig, title, height=420)


def payment_shipping_charts(payment_df, shipping_df):
    fig1 = px.bar(payment_df, x="orders", y="payment_method", orientation="h",
                   color="orders", color_continuous_scale="Tealgrn", text_auto=True)
    fig1.update_layout(coloraxis_showscale=False)
    fig1.update_xaxes(title="Orders")
    fig1.update_yaxes(title=None)
    fig1 = _apply_base(fig1, "Orders by Payment Method", height=320)

    fig2 = px.bar(shipping_df, x="orders", y="ship_mode", orientation="h",
                   color="orders", color_continuous_scale="Teal", text_auto=True)
    fig2.update_layout(coloraxis_showscale=False)
    fig2.update_xaxes(title="Orders")
    fig2.update_yaxes(title=None)
    fig2 = _apply_base(fig2, "Orders by Shipping Mode", height=320)

    return fig1, fig2
