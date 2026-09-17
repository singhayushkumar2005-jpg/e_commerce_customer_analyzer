"""
analytics.py
------------
Core analytical functions: KPIs, trend aggregation, product performance,
customer segmentation (including RFM), and sales anomaly detection.

All functions take an already-cleaned, feature-engineered DataFrame
(as produced by preprocessing.load_and_prepare_data) and return
summary DataFrames or dicts ready to hand to the dashboard/plotting layer.
"""

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# KPIs
# --------------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame) -> dict:
    """Headline KPIs. Excludes cancelled/returned orders from revenue & profit
    (they represent no realized sale), but reports their counts separately."""
    valid = df[~df["is_cancelled_or_returned"]]

    total_orders = df["order_id"].nunique()
    total_revenue = valid["net_sales"].sum()
    total_profit = valid["profit"].sum()
    total_units = valid["quantity"].sum()
    aov = valid.groupby("order_id")["net_sales"].sum().mean() if valid["order_id"].nunique() > 0 else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    total_customers = df["customer_id"].nunique()
    cancelled_returned = df[df["is_cancelled_or_returned"]]["order_id"].nunique()
    cancellation_rate = (cancelled_returned / total_orders * 100) if total_orders > 0 else 0

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "total_units_sold": total_units,
        "avg_order_value": aov,
        "profit_margin_pct": profit_margin,
        "total_customers": total_customers,
        "cancellation_return_rate_pct": cancellation_rate,
    }


# --------------------------------------------------------------------------
# Trends
# --------------------------------------------------------------------------

def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    trend = (
        valid.groupby("order_year_month")
        .agg(
            revenue=("net_sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("order_year_month")
    )
    trend["avg_order_value"] = trend["revenue"] / trend["orders"].replace(0, np.nan)
    return trend


def weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    trend = (
        valid.groupby("order_week")
        .agg(
            revenue=("net_sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("order_week")
    )
    return trend


# --------------------------------------------------------------------------
# Product performance
# --------------------------------------------------------------------------

def category_sales(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    out = (
        valid.groupby(["category", "sub_category"])
        .agg(revenue=("net_sales", "sum"), profit=("profit", "sum"), units=("quantity", "sum"),
             orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    return out


def top_products(df: pd.DataFrame, n=10, by="net_sales") -> pd.DataFrame:
    """by: 'net_sales' for best-selling by revenue, 'profit' for most profitable,
    'quantity' for best-selling by units."""
    valid = df[~df["is_cancelled_or_returned"]]
    grouped = (
        valid.groupby(["product_id", "product_name", "category", "sub_category"])
        .agg(revenue=("net_sales", "sum"), profit=("profit", "sum"), units=("quantity", "sum"),
             orders=("order_id", "nunique"))
        .reset_index()
    )
    sort_col = {"net_sales": "revenue", "profit": "profit", "quantity": "units"}.get(by, "revenue")
    return grouped.sort_values(sort_col, ascending=False).head(n)


# --------------------------------------------------------------------------
# Geography & order status
# --------------------------------------------------------------------------

def sales_by_region(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    return (
        valid.groupby("region")
        .agg(revenue=("net_sales", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"),
             customers=("customer_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )


def sales_by_country(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    return (
        valid.groupby("country")
        .agg(revenue=("net_sales", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )


def order_status_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.drop_duplicates(subset=["order_id"])
        .groupby("order_status")
        .agg(orders=("order_id", "nunique"))
        .reset_index()
    )
    out["pct"] = out["orders"] / out["orders"].sum() * 100
    return out.sort_values("orders", ascending=False)


# --------------------------------------------------------------------------
# Customer segmentation
# --------------------------------------------------------------------------

def new_vs_returning(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    out = (
        valid.drop_duplicates(subset=["order_id"])
        .groupby("customer_type")
        .agg(orders=("order_id", "nunique"))
        .reset_index()
    )
    revenue = (
        valid.groupby("customer_type")["net_sales"].sum().reset_index().rename(columns={"net_sales": "revenue"})
    )
    out = out.merge(revenue, on="customer_type", how="left")
    out["pct_of_orders"] = out["orders"] / out["orders"].sum() * 100
    return out


def customer_spending_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Simple spend/frequency-based segmentation (Low/Medium/High/VIP) using quartiles."""
    valid = df[~df["is_cancelled_or_returned"]]
    cust = (
        valid.groupby("customer_id")
        .agg(total_spend=("net_sales", "sum"), orders=("order_id", "nunique"))
        .reset_index()
    )
    cust["avg_order_value"] = cust["total_spend"] / cust["orders"]

    try:
        cust["spend_segment"] = pd.qcut(
            cust["total_spend"], q=4, labels=["Low", "Medium", "High", "VIP"]
        )
    except ValueError:
        cust["spend_segment"] = "Medium"

    return cust


# --------------------------------------------------------------------------
# RFM Segmentation
# --------------------------------------------------------------------------

def compute_rfm(df: pd.DataFrame, snapshot_date=None) -> pd.DataFrame:
    """
    Recency, Frequency, Monetary segmentation.
    - Recency: days since last purchase (lower = better)
    - Frequency: number of distinct orders
    - Monetary: total net sales

    Scores each 1-5 (5 = best) via quantile binning, combines into RFM segment labels.
    """
    valid = df[~df["is_cancelled_or_returned"]].copy()
    if snapshot_date is None:
        snapshot_date = valid["order_date"].max() + pd.Timedelta(days=1)

    rfm = (
        valid.groupby("customer_id")
        .agg(
            last_purchase=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("net_sales", "sum"),
        )
        .reset_index()
    )
    rfm["recency"] = (snapshot_date - rfm["last_purchase"]).dt.days

    def safe_qcut_score(series, ascending_is_better):
        """Return 1-5 scores; for recency, lower value = better = higher score."""
        try:
            ranks = series.rank(method="first")
            bins = pd.qcut(ranks, q=5, labels=[1, 2, 3, 4, 5])
            scores = bins.astype(int)
        except ValueError:
            scores = pd.Series(3, index=series.index)
        if not ascending_is_better:
            scores = 6 - scores
        return scores

    rfm["R_score"] = safe_qcut_score(rfm["recency"], ascending_is_better=False)  # low recency -> high score
    rfm["F_score"] = safe_qcut_score(rfm["frequency"], ascending_is_better=True)
    rfm["M_score"] = safe_qcut_score(rfm["monetary"], ascending_is_better=True)
    rfm["RFM_score"] = rfm["R_score"].astype(str) + rfm["F_score"].astype(str) + rfm["M_score"].astype(str)
    rfm["RFM_total"] = rfm[["R_score", "F_score", "M_score"]].sum(axis=1)

    def segment_label(row):
        r, f, m = row["R_score"], row["F_score"], row["M_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        if r >= 4 and f <= 2:
            return "New Customers"
        if r >= 3 and f <= 2 and m <= 2:
            return "Potential Loyalists"
        if r <= 2 and f >= 4:
            return "At Risk"
        if r <= 2 and f >= 3 and m >= 3:
            return "Can't Lose Them"
        if r <= 2 and f <= 2 and m <= 2:
            return "Hibernating"
        if r <= 2:
            return "About to Sleep"
        return "Need Attention"

    rfm["segment"] = rfm.apply(segment_label, axis=1)
    return rfm


def rfm_segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    out = (
        rfm_df.groupby("segment")
        .agg(
            customers=("customer_id", "nunique"),
            avg_recency_days=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_monetary=("monetary", "sum"),
        )
        .reset_index()
        .sort_values("total_monetary", ascending=False)
    )
    return out


# --------------------------------------------------------------------------
# Anomaly detection
# --------------------------------------------------------------------------

def detect_sales_anomalies(daily_or_monthly_trend: pd.DataFrame, value_col="revenue", z_thresh=2.0,
                            window=7) -> pd.DataFrame:
    """
    Flags anomalies in a time-ordered revenue/orders series using a rolling
    z-score method (robust to trend/seasonality drift better than a global
    z-score, since it compares each point to its local neighborhood).
    """
    out = daily_or_monthly_trend.copy().reset_index(drop=True)
    if len(out) < max(window, 5):
        out["rolling_mean"] = out[value_col]
        out["rolling_std"] = 0
        out["z_score"] = 0
        out["is_anomaly"] = False
        out["anomaly_type"] = "Normal"
        return out

    out["rolling_mean"] = out[value_col].rolling(window=window, min_periods=3, center=True).mean()
    out["rolling_std"] = out[value_col].rolling(window=window, min_periods=3, center=True).std()
    out["rolling_mean"] = out["rolling_mean"].bfill().ffill()
    out["rolling_std"] = out["rolling_std"].replace(0, np.nan).bfill().ffill().fillna(1)

    out["z_score"] = (out[value_col] - out["rolling_mean"]) / out["rolling_std"]
    out["is_anomaly"] = out["z_score"].abs() >= z_thresh
    out["anomaly_type"] = np.where(
        out["is_anomaly"] & (out["z_score"] > 0), "Spike",
        np.where(out["is_anomaly"] & (out["z_score"] < 0), "Drop", "Normal")
    )
    return out


def daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[~df["is_cancelled_or_returned"]]
    trend = (
        valid.groupby(valid["order_date"].dt.date)
        .agg(revenue=("net_sales", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        .reset_index()
        .rename(columns={"order_date": "date"})
        .sort_values("date")
    )
    return trend


# --------------------------------------------------------------------------
# Customer purchase behavior
# --------------------------------------------------------------------------

def purchase_behavior_summary(df: pd.DataFrame) -> dict:
    valid = df[~df["is_cancelled_or_returned"]]
    orders_per_customer = valid.groupby("customer_id")["order_id"].nunique()
    items_per_order = valid.groupby("order_id")["quantity"].sum()

    repeat_customers = (orders_per_customer > 1).sum()
    total_customers = orders_per_customer.shape[0]
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0

    return {
        "avg_orders_per_customer": orders_per_customer.mean(),
        "avg_items_per_order": items_per_order.mean(),
        "repeat_purchase_rate_pct": repeat_rate,
        "median_orders_per_customer": orders_per_customer.median(),
    }


def preferred_payment_and_shipping(df: pd.DataFrame) -> tuple:
    payment = (
        df.drop_duplicates(subset=["order_id"])
        .groupby("payment_method")["order_id"].nunique()
        .reset_index(name="orders")
        .sort_values("orders", ascending=False)
    )
    shipping = (
        df.drop_duplicates(subset=["order_id"])
        .groupby("ship_mode")["order_id"].nunique()
        .reset_index(name="orders")
        .sort_values("orders", ascending=False)
    )
    return payment, shipping
