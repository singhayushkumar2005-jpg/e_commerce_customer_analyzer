"""
preprocessing.py
-----------------
Data loading, cleaning, validation, and feature engineering for the
e-commerce analytics dashboard.

The main entry point is `load_and_prepare_data()`, which returns a single
merged, cleaned, feature-enriched DataFrame ready for analysis, plus the
cleaned customers and products tables.
"""

import os
import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_raw_data(data_dir=DATA_DIR):
    """Load the raw CSVs. Generates them first if they don't exist yet."""
    orders_path = os.path.join(data_dir, "orders.csv")
    customers_path = os.path.join(data_dir, "customers.csv")
    products_path = os.path.join(data_dir, "products.csv")

    if not (os.path.exists(orders_path) and os.path.exists(customers_path) and os.path.exists(products_path)):
        # Lazy import to avoid circular import issues when this module is used standalone
        from data_generator import build_dataset
        build_dataset(output_dir=data_dir)

    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    customers = pd.read_csv(customers_path, parse_dates=["signup_date"])
    products = pd.read_csv(products_path)

    return orders, customers, products


# --------------------------------------------------------------------------
# Cleaning
# --------------------------------------------------------------------------

def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()

    # Drop exact duplicate line items
    df = df.drop_duplicates()

    # Remove rows with impossible / missing critical values
    df = df.dropna(subset=["order_id", "order_date", "customer_id", "product_id", "quantity", "net_sales"])
    df = df[df["quantity"] > 0]
    df = df[df["unit_price"] >= 0]
    df = df[df["net_sales"] >= 0]

    # Cap extreme outliers in net_sales using percentile fencing (cap, don't drop,
    # so we don't lose whole orders). We only cap net_sales directly, then
    # re-derive profit from the (possibly capped) net_sales and unchanged
    # total_cost, so profit = net_sales - total_cost stays internally
    # consistent for every row instead of drifting out of sync.
    lower_fence = df["net_sales"].quantile(0.001)
    upper_fence = df["net_sales"].quantile(0.99) * 1.5
    df["net_sales"] = df["net_sales"].clip(lower=lower_fence, upper=upper_fence)
    df["profit"] = df["net_sales"] - df["total_cost"]

    df["order_status"] = df["order_status"].str.strip().str.title()
    df["payment_method"] = df["payment_method"].str.strip()
    df["category"] = df["category"].str.strip()
    df["sub_category"] = df["sub_category"].str.strip()

    df = df.reset_index(drop=True)
    return df


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    df = df.drop_duplicates(subset=["customer_id"])
    df = df.dropna(subset=["customer_id", "signup_date"])
    df["age"] = df["age"].clip(lower=16, upper=90)
    return df.reset_index(drop=True)


def clean_products(products: pd.DataFrame) -> pd.DataFrame:
    df = products.copy()
    df = df.drop_duplicates(subset=["product_id"])
    df = df.dropna(subset=["product_id", "unit_price", "unit_cost"])
    df = df[df["unit_price"] > 0]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# Feature engineering
# --------------------------------------------------------------------------

def engineer_order_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar and order-level derived features to the line-item table."""
    df = df.copy()
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["order_month_name"] = df["order_date"].dt.strftime("%b")
    df["order_year_month"] = df["order_date"].dt.to_period("M").astype(str)
    df["order_week"] = df["order_date"].dt.to_period("W").apply(lambda p: p.start_time.date().isoformat())
    df["order_weekday"] = df["order_date"].dt.day_name()
    df["order_quarter"] = df["order_date"].dt.to_period("Q").astype(str)
    df["is_cancelled_or_returned"] = df["order_status"].isin(["Cancelled", "Returned"])
    df["margin_pct"] = np.where(df["net_sales"] > 0, df["profit"] / df["net_sales"], 0)
    return df


def merge_full_dataset(orders: pd.DataFrame, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Join line items with customer attributes (product attrs already on orders)."""
    df = orders.merge(
        customers[["customer_id", "customer_name", "gender", "age", "signup_date", "acquisition_channel"]],
        on="customer_id", how="left"
    )
    return df


def add_customer_order_sequence(df: pd.DataFrame) -> pd.DataFrame:
    """Flags each order as 'New' (customer's first order) or 'Returning'.

    Ranks each customer's distinct orders by order_date (ties broken by
    order_id for stability, since a customer can place more than one order
    on the same calendar day). is_first_order and customer_type are both
    derived from this single ranking so they can never disagree with
    each other, even when same-day repeat orders are present.
    """
    df = df.copy()
    unique_orders = df.drop_duplicates(subset=["order_id"]).sort_values(["customer_id", "order_date", "order_id"])
    order_rank = unique_orders.groupby("customer_id").cumcount()
    order_rank_map = dict(zip(unique_orders["order_id"], order_rank))

    df["customer_order_sequence"] = df["order_id"].map(order_rank_map)
    df["is_first_order"] = df["customer_order_sequence"] == 0
    df["customer_type"] = np.where(df["is_first_order"], "New", "Returning")
    return df


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

def load_and_prepare_data(data_dir=DATA_DIR):
    """
    Full pipeline: load -> clean -> engineer features -> merge.
    Returns (full_df, customers_df, products_df)
    """
    orders_raw, customers_raw, products_raw = load_raw_data(data_dir)

    orders = clean_orders(orders_raw)
    customers = clean_customers(customers_raw)
    products = clean_products(products_raw)

    full_df = merge_full_dataset(orders, customers, products)
    full_df = engineer_order_features(full_df)
    full_df = add_customer_order_sequence(full_df)

    return full_df, customers, products


if __name__ == "__main__":
    full_df, customers, products = load_and_prepare_data()
    print(full_df.shape)
    print(full_df.dtypes)
    print(full_df.head())
