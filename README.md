# 🛍️ E-Commerce Sales & Customer Analytics Dashboard

A full-featured, interactive analytics dashboard for e-commerce sales, customer behavior, and profitability — built with **Python, Pandas, NumPy, Plotly, and Streamlit**.

The project includes a synthetic-but-realistic dataset generator, a complete data cleaning & feature engineering pipeline, an analytics layer (KPIs, RFM segmentation, anomaly detection), and a polished, filterable multi-tab dashboard.

> Built as a portfolio-ready data analytics project demonstrating end-to-end skills: data generation, cleaning, EDA, feature engineering, statistical segmentation, and interactive visualization.

---

## 📸 Screenshots

> Add your own screenshots here after running the app locally (see [How to Run](#-how-to-run-locally) below).
> Suggested shots: `Overview` tab, `RFM Segmentation` tab, `Anomaly Detection` tab.

| Overview | RFM Segmentation | Anomaly Detection |
|---|---|---|
| `assets/screenshot_overview.png` | `assets/screenshot_rfm.png` | `assets/screenshot_anomaly.png` |

To capture your own: run the app locally, take a screenshot of each tab, and drop the images into the `assets/` folder using the filenames above (or update the paths in this README).

---

## ✨ Features

### Core Analytics
- **KPI cards**: Total Revenue, Total Profit, Total Orders, Average Order Value, Profit Margin %, Cancellation/Return Rate
- **Monthly & weekly sales/revenue trends** with toggleable granularity
- **Sales by category and sub-category** (bar chart + interactive treemap)
- **Top 10 best-selling and most profitable products**, switchable by revenue / profit / units sold
- **New vs. returning customer** breakdown (by order share and revenue)
- **Sales by region and country** (bar chart + world choropleth map)
- **Order status analysis** (Delivered / Shipped / Processing / Cancelled / Returned)
- **Customer purchase behavior**: repeat purchase rate, avg orders/customer, avg items/order, payment & shipping preferences
- **Profit and revenue analysis** across every dimension above

### Advanced Analytics
- **RFM customer segmentation** — Recency, Frequency, Monetary scoring (1–5 scale) with rule-based segment labels: *Champions, Loyal Customers, At Risk, Can't Lose Them, Hibernating, New Customers,* etc. Includes a segment summary table and an interactive Recency-vs-Frequency bubble chart (bubble size = Monetary value).
- **Sales anomaly detection** — rolling z-score method that flags revenue **spikes** and **drops** relative to a local moving average, with adjustable sensitivity and window size directly in the UI.
- **Customer spending segmentation** — quartile-based Low / Medium / High / VIP tiers.

### Interactivity
- Sidebar filters for **date range, category, region, order status, and customer type** — every chart and KPI updates live
- Hover tooltips on every chart
- Expandable detail tables for deep-dives without cluttering the main view
- Clean, modern, responsive layout with a custom light theme

---

## 🗂️ Project Structure

```
ecommerce-analytics-dashboard/
│
├── data/                       # Generated CSV dataset (created on first run)
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
│
├── src/
│   ├── data_generator.py       # Synthetic dataset generation (customers, products, orders)
│   ├── preprocessing.py        # Loading, cleaning, validation, feature engineering
│   ├── analytics.py            # KPIs, trends, RFM segmentation, anomaly detection
│   ├── visualization.py        # Reusable Plotly chart builders
│   └── app.py                  # Streamlit dashboard (main entry point)
│
├── assets/                     # Screenshots for this README
├── .streamlit/
│   └── config.toml             # Dashboard theme configuration
├── requirements.txt
├── .gitignore
└── README.md
```

**Design rationale:** each pipeline stage is isolated into its own module (generation → preprocessing → analytics → visualization → app), so any layer can be tested, reused, or swapped independently — e.g., you could point `preprocessing.py` at a real e-commerce export instead of the synthetic generator without touching the dashboard code at all.

---

## 📊 Dataset

Since a real proprietary e-commerce dataset isn't available for public sharing, this project **generates a realistic synthetic dataset** on first run (`src/data_generator.py`), seeded for reproducibility (`random_seed=42`).

| Table | Rows | Description |
|---|---|---|
| `customers.csv` | ~1,200 | Customer ID, name, gender, age, region, country, signup date, acquisition channel |
| `products.csv` | ~260 | Product ID, name, category, sub-category, unit cost, unit price |
| `orders.csv` | ~19,000 line items across 9,000 orders | Order/product/customer IDs, quantities, discounts, gross/net sales, cost, profit, order status, payment method, shipping mode, order date |

**Realism features baked into the generator:**
- 7 product categories × 5 sub-categories each, with category-appropriate pricing and margin ranges
- Seasonal demand boost in November/December (holiday shopping) and a dip in February
- Power-law customer purchase propensity (a small share of customers drive a disproportionate share of orders — mirrors real retail Pareto behavior)
- Randomized discounts, order statuses (weighted toward "Delivered"), payment methods, and shipping modes
- Orders always occur on or after each customer's signup date (referential integrity)

Want to use your **own data** instead? Replace the CSVs in `data/` with your own files using the same column schema, or point `preprocessing.load_raw_data()` at a different path — the rest of the pipeline works unchanged as long as column names match.

---

## 🧪 Methodology

1. **Data Generation** (`data_generator.py`) — builds three related tables with realistic distributions and referential integrity.
2. **Data Cleaning** (`preprocessing.py`) — drops duplicates, removes/repairs invalid rows (negative prices, missing IDs), caps outliers in revenue/profit via IQR-based fencing, and standardizes categorical text fields.
3. **Feature Engineering** (`preprocessing.py`) — derives calendar features (year, month, week, quarter, weekday), margin %, cancelled/returned flags, and a per-customer order sequence used to classify **New vs. Returning** orders.
4. **Analytics** (`analytics.py`) — pure functions that aggregate the cleaned data into KPIs, trends, product/category/region rollups, RFM scores, and anomaly flags. Cancelled/returned orders are excluded from revenue and profit calculations (no realized sale) but tracked separately in the cancellation rate KPI.
5. **Visualization** (`visualization.py`) — a library of Plotly chart builders with a consistent color palette and styling, kept separate from layout/app logic.
6. **Dashboard** (`app.py`) — Streamlit app that wires filters → analytics → charts, with `st.cache_data` so the (moderately expensive) load/clean/engineer pipeline only runs once per session.

### RFM Segmentation Logic
Each customer is scored 1–5 (5 = best) on:
- **Recency** — days since their last order (lower is better → higher score)
- **Frequency** — number of distinct orders (higher is better)
- **Monetary** — total net sales (higher is better)

Scores are combined into a 3-digit `RFM_score` (e.g. `"555"` = best possible) and mapped to human-readable segments (Champions, Loyal Customers, At Risk, Hibernating, etc.) using standard RFM business rules.

### Anomaly Detection Logic
Daily revenue is compared against a **centered rolling mean and standard deviation** (default 7-day window). Any day whose z-score exceeds the chosen threshold (default ±2.0) is flagged as a **Spike** (positive) or **Drop** (negative). The rolling approach adapts to trend/seasonality drift better than a single global z-score would.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Data generation & manipulation | Python, Pandas, NumPy |
| Visualization | Plotly (Express & Graph Objects) |
| Dashboard framework | Streamlit |
| Segmentation & stats | Pandas (`qcut` quantile binning), rolling z-score |

---

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/ecommerce-analytics-dashboard.git
cd ecommerce-analytics-dashboard
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Generate the dataset manually
The dashboard auto-generates the dataset on first run if it's missing, but you can also do it explicitly:
```bash
python src/data_generator.py
```
This creates `customers.csv`, `products.csv`, and `orders.csv` inside `data/`.

### 5. Launch the dashboard
```bash
streamlit run src/app.py
```

Streamlit will open the dashboard in your browser automatically (default: `http://localhost:8501`).

---

## 📦 Requirements

```
streamlit>=1.35.0
pandas>=2.2.0
numpy>=1.26.0
plotly>=5.22.0
```

Install with `pip install -r requirements.txt`.

---

## 🔍 Exploring the Code

- Want to change the dataset size? Edit `N_CUSTOMERS`, `N_PRODUCTS`, `N_ORDERS` at the top of `src/data_generator.py`.
- Want to adjust RFM segment rules? See `segment_label()` inside `compute_rfm()` in `src/analytics.py`.
- Want to tune anomaly sensitivity defaults? See `detect_sales_anomalies()` in `src/analytics.py` — the UI sliders in the "Anomaly Detection" tab already expose this at runtime.
- Want a different color theme? Edit `.streamlit/config.toml` and the palette constants at the top of `src/visualization.py`.

---

## 📄 License

This project is provided as-is for portfolio and educational use. Feel free to fork, modify, and use it as a starting point for your own analytics projects.

---

## 🙋 About

Built as a demonstration of an end-to-end data analytics workflow — from synthetic data generation through cleaning, feature engineering, statistical segmentation (RFM), anomaly detection, and interactive dashboarding — using a modern Python data stack.
