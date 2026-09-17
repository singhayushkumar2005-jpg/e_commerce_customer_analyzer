"""
data_generator.py
------------------
Generates a realistic, internally-consistent synthetic e-commerce dataset:
customers, products, and orders (with order line items).

Run directly to (re)build the CSV dataset used by the rest of the project:

    python src/data_generator.py

The generator uses a fixed random seed so the dataset is reproducible.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------

CATEGORIES = {
    "Electronics": ["Smartphones", "Laptops", "Headphones", "Cameras", "Accessories"],
    "Fashion": ["Men's Clothing", "Women's Clothing", "Footwear", "Watches", "Bags"],
    "Home & Kitchen": ["Furniture", "Cookware", "Home Decor", "Appliances", "Bedding"],
    "Beauty & Personal Care": ["Skincare", "Haircare", "Makeup", "Fragrances", "Grooming"],
    "Sports & Outdoors": ["Fitness Equipment", "Cycling", "Camping Gear", "Sportswear", "Yoga"],
    "Books & Stationery": ["Fiction", "Non-Fiction", "Notebooks", "Office Supplies", "Kids Books"],
    "Toys & Games": ["Action Figures", "Board Games", "Puzzles", "Outdoor Toys", "Educational Toys"],
}

REGIONS = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["United Kingdom", "Germany", "France", "Spain", "Italy"],
    "Asia Pacific": ["India", "China", "Japan", "Australia", "Singapore"],
    "South America": ["Brazil", "Argentina", "Chile"],
    "Middle East & Africa": ["United Arab Emirates", "Saudi Arabia", "South Africa"],
}

ORDER_STATUSES = ["Delivered", "Shipped", "Processing", "Cancelled", "Returned"]
ORDER_STATUS_WEIGHTS = [0.72, 0.10, 0.06, 0.06, 0.06]

PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI/Wallet", "Net Banking", "Cash on Delivery", "PayPal"]
PAYMENT_WEIGHTS = [0.30, 0.18, 0.20, 0.10, 0.12, 0.10]

SHIP_MODES = ["Standard", "Express", "Same-Day"]
SHIP_WEIGHTS = [0.65, 0.28, 0.07]

FIRST_NAMES = [
    "Aarav", "Priya", "James", "Emma", "Liam", "Olivia", "Noah", "Sophia", "Ravi", "Ananya",
    "William", "Isabella", "Chen", "Mei", "Carlos", "Sofia", "Lucas", "Mia", "Arjun", "Diya",
    "Ethan", "Amelia", "Mohammed", "Fatima", "Daniel", "Grace", "Kenji", "Yuki", "Omar", "Layla",
]
LAST_NAMES = [
    "Sharma", "Smith", "Johnson", "Patel", "Williams", "Brown", "Kumar", "Garcia", "Miller", "Davis",
    "Rodriguez", "Wilson", "Li", "Wang", "Silva", "Martinez", "Singh", "Anderson", "Khan", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Nakamura", "Ibrahim", "Clark", "Lewis",
]

PRODUCT_ADJECTIVES = ["Premium", "Classic", "Pro", "Essential", "Deluxe", "Compact", "Ultra", "Everyday", "Smart", "Eco"]

# Category -> (min_cost, max_cost, min_margin_pct, max_margin_pct)
CATEGORY_PRICE_PROFILE = {
    "Electronics": (40, 900, 0.10, 0.28),
    "Fashion": (8, 150, 0.30, 0.55),
    "Home & Kitchen": (10, 400, 0.20, 0.40),
    "Beauty & Personal Care": (4, 90, 0.35, 0.60),
    "Sports & Outdoors": (10, 300, 0.20, 0.42),
    "Books & Stationery": (2, 40, 0.15, 0.35),
    "Toys & Games": (5, 120, 0.25, 0.45),
}

N_CUSTOMERS = 1200
N_PRODUCTS = 260
N_ORDERS = 9000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)


def _random_dates(n, start, end):
    delta_days = (end - start).days
    offsets = np.random.randint(0, delta_days + 1, size=n)
    return [start + timedelta(days=int(d)) for d in offsets]


def generate_customers(n=N_CUSTOMERS):
    rows = []
    for cid in range(1, n + 1):
        first = np.random.choice(FIRST_NAMES)
        last = np.random.choice(LAST_NAMES)
        region = np.random.choice(list(REGIONS.keys()))
        country = np.random.choice(REGIONS[region])
        signup_date = _random_dates(1, START_DATE, END_DATE - timedelta(days=1))[0]
        age = int(np.clip(np.random.normal(35, 11), 18, 75))
        gender = np.random.choice(["Male", "Female", "Other"], p=[0.48, 0.48, 0.04])
        acquisition = np.random.choice(
            ["Organic Search", "Paid Ads", "Social Media", "Referral", "Email Campaign", "Direct"],
            p=[0.28, 0.22, 0.20, 0.12, 0.10, 0.08],
        )
        rows.append({
            "customer_id": f"CUST{cid:05d}",
            "customer_name": f"{first} {last}",
            "gender": gender,
            "age": age,
            "region": region,
            "country": country,
            "signup_date": signup_date,
            "acquisition_channel": acquisition,
        })
    return pd.DataFrame(rows)


def generate_products(n=N_PRODUCTS):
    rows = []
    pid = 1
    categories = list(CATEGORIES.keys())
    # Ensure reasonably even spread across categories/sub-categories
    per_cat = max(1, n // len(categories))
    for cat in categories:
        subcats = CATEGORIES[cat]
        cost_min, cost_max, margin_min, margin_max = CATEGORY_PRICE_PROFILE[cat]
        for _ in range(per_cat):
            subcat = np.random.choice(subcats)
            adj = np.random.choice(PRODUCT_ADJECTIVES)
            product_name = f"{adj} {subcat[:-1] if subcat.endswith('s') else subcat} {np.random.randint(100, 999)}"
            unit_cost = round(np.random.uniform(cost_min, cost_max), 2)
            margin_pct = np.random.uniform(margin_min, margin_max)
            unit_price = round(unit_cost / (1 - margin_pct), 2)
            rows.append({
                "product_id": f"PROD{pid:05d}",
                "product_name": product_name,
                "category": cat,
                "sub_category": subcat,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
            })
            pid += 1
    return pd.DataFrame(rows)


def generate_orders(customers_df, products_df, n_orders=N_ORDERS):
    rows = []
    customer_ids = customers_df["customer_id"].values
    customer_signup = dict(zip(customers_df["customer_id"], customers_df["signup_date"]))
    customer_region = dict(zip(customers_df["customer_id"], customers_df["region"]))
    customer_country = dict(zip(customers_df["customer_id"], customers_df["country"]))

    # Give some customers much higher purchase propensity (realistic skew: power users)
    propensity = np.random.gamma(shape=1.6, scale=1.0, size=len(customer_ids))
    propensity = propensity / propensity.sum()

    order_id_counter = 1
    for _ in range(n_orders):
        cust_id = np.random.choice(customer_ids, p=propensity)
        signup = customer_signup[cust_id]
        # order date must be on/after signup date
        latest = END_DATE
        if signup >= latest:
            order_date = signup
        else:
            order_date = _random_dates(1, signup, latest)[0]

        # seasonal boost: Nov/Dec (holiday), slight dip in Feb
        month = order_date.month
        seasonal_multiplier = {11: 1.4, 12: 1.6, 2: 0.8}.get(month, 1.0)

        n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.28, 0.16, 0.10, 0.06])
        products_in_order = products_df.sample(n=n_items, replace=False)

        status = np.random.choice(ORDER_STATUSES, p=ORDER_STATUS_WEIGHTS)
        payment = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
        ship_mode = np.random.choice(SHIP_MODES, p=SHIP_WEIGHTS)

        order_id = f"ORD{order_id_counter:06d}"
        order_id_counter += 1

        for _, prod in products_in_order.iterrows():
            qty = np.random.choice([1, 2, 3, 4], p=[0.55, 0.25, 0.12, 0.08])
            qty = max(1, int(round(qty * min(seasonal_multiplier, 1.3))))
            discount_pct = np.random.choice(
                [0.0, 0.05, 0.10, 0.15, 0.20, 0.30],
                p=[0.45, 0.15, 0.15, 0.12, 0.08, 0.05],
            )
            gross_sales = round(prod["unit_price"] * qty, 2)
            discount_amount = round(gross_sales * discount_pct, 2)
            net_sales = round(gross_sales - discount_amount, 2)
            total_cost = round(prod["unit_cost"] * qty, 2)
            profit = round(net_sales - total_cost, 2)

            rows.append({
                "order_id": order_id,
                "order_date": order_date,
                "customer_id": cust_id,
                "region": customer_region[cust_id],
                "country": customer_country[cust_id],
                "product_id": prod["product_id"],
                "product_name": prod["product_name"],
                "category": prod["category"],
                "sub_category": prod["sub_category"],
                "quantity": qty,
                "unit_price": prod["unit_price"],
                "unit_cost": prod["unit_cost"],
                "discount_pct": discount_pct,
                "gross_sales": gross_sales,
                "discount_amount": discount_amount,
                "net_sales": net_sales,
                "total_cost": total_cost,
                "profit": profit,
                "order_status": status,
                "payment_method": payment,
                "ship_mode": ship_mode,
            })

    return pd.DataFrame(rows)


DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def build_dataset(output_dir=None):
    if output_dir is None:
        output_dir = DEFAULT_DATA_DIR
    os.makedirs(output_dir, exist_ok=True)

    print("Generating customers...")
    customers = generate_customers()

    print("Generating products...")
    products = generate_products()

    print("Generating orders (this creates the main fact table)...")
    orders = generate_orders(customers, products)

    customers.to_csv(os.path.join(output_dir, "customers.csv"), index=False)
    products.to_csv(os.path.join(output_dir, "products.csv"), index=False)
    orders.to_csv(os.path.join(output_dir, "orders.csv"), index=False)

    print(f"Done. {len(customers)} customers, {len(products)} products, "
          f"{orders['order_id'].nunique()} orders, {len(orders)} order line items.")
    print(f"Files written to '{output_dir}/'")

    return customers, products, orders


if __name__ == "__main__":
    build_dataset()
