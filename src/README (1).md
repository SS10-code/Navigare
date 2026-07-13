# 🧭 Navigare — Local Retail Analytics Dashboard

> **Phase 3 · Week 7** — Back-end Algorithm Engineering  
> A rule-based retail intelligence system for local store owners. No ML black boxes. Every number is traceable to a formula.

---

## What It Does

Navigare turns raw transaction and inventory CSVs into a fully interactive analytics dashboard — forecasting sales, flagging reorder alerts, scoring SEO copy, and identifying your best customers.

| Page | What you get |
|---|---|
| 📊 Overview | Revenue over time, store channel split, top products |
| 📦 Inventory Health | MAD, Safety Stock, Reorder Point per SKU |
| 🛒 What Sells Together | Market basket pairs (Support, Confidence, Lift) |
| 👥 Customer Segments | RFM scoring: Champion → At Risk |
| 📈 Sales Forecast | SMA · EMA · Holt-Winters with 14-day projection |
| 🔍 SEO Auditor | Paste web copy → keyword density score with penalty curve |
| 🔬 Under the Hood | Z-Score, cyclic encoding, lag features, VIF, ADF test |
| 📖 Glossary | 30-term plain-English reference |

---

## Run Order

```bash
# 1. Install dependencies
pip install streamlit pandas numpy faker statsmodels plotly

# 2. Seed raw data
python generate_mock_data.py

# 3. Map + merge the two real-world datasets (Olist BRL + UCI GBP → USD)
python schema_mapper.py

# 4. Inject anomalies + test pipeline resilience
python chaos_monkey.py

# 5. Build feature matrix (EMA, lags, cyclic encoding, VIF, ADF)
python feature_engineering.py

# 6. Compute all business metrics (MAD, ROP, Safety Stock, RFM, Combos)
python business_metrics.py

# 7. Launch dashboard
streamlit run dashboard.py
```

---

## File Structure

```
Navigare/
├── generate_mock_data.py     ← Seeds inventory, transactions, customers CSVs
├── schema_mapper.py          ← Merges Olist (BRL) + UCI (GBP) into unified USD schema
├── chaos_monkey.py           ← Injects 7 anomaly types at 2% rate, verifies cleaner
├── feature_engineering.py    ← EMA · Z-Score · cyclic encoding · lags · VIF · ADF
├── business_metrics.py       ← MAD · Safety Stock · ROP · RFM · Market Basket
├── seo_engine.py             ← Text normalisation · sliding window N-gram · density scoring
├── dashboard.py              ← Streamlit app (8 pages, sidebar navigation)
│
└── data/
    ├── raw/
    │   ├── inventory.csv
    │   ├── transactions.csv
    │   ├── customers.csv
    │   └── inventory_corrupted.csv
    └── clean/
        ├── unified_transactions.csv
        ├── inventory_clean.csv
        ├── inventory_metrics.csv     ← MAD + Safety Stock + ROP
        ├── product_metrics.csv       ← Margin + Sell-Through
        ├── customer_rfm.csv          ← RFM scores + segments
        ├── combo_pairs.csv           ← Market basket pairs
        ├── features.csv              ← Full 39-column feature matrix
        ├── ema_forecast.csv          ← 14-day EMA projection
        ├── vif_results.csv
        ├── adf_results.csv
        └── chaos_report.json
```

---

## Key Algorithms

### MAD → Safety Stock → ROP (Inventory)

```python
# Mean Absolute Deviation — demand variability per product
MAD = mean(|daily_demand - avg_demand|)

# Safety Stock — buffer for demand spikes during lead time
# Z=1.65 targets 95% service level (in-stock 95% of the time)
Safety_Stock = Z * MAD * sqrt(Lead_Time_Days)

# Reorder Point — trigger level to place a supplier order
ROP = (Avg_Daily_Demand * Lead_Time_Days) + Safety_Stock
```

### SEO Density Scoring (Piecewise Non-Linear)

```python
# Inverted-U curve — rewards the sweet spot, penalises stuffing
if density < 1.0%:
    score = 50          # Under-optimized — crawler can't associate page with keyword

elif density <= 3.5%:
    score = 100         # Sweet spot — human-authored content, crawler trusts the page

else:
    excess = density - 3.5
    score = max(0, int(100 - (excess * 15)))   # Hard floor prevents negative scores
```

**7.5% stress test:** excess = 4.0 → penalty = 60 → score = 40 → high-severity warning  
**10.2% extreme:** excess = 6.7 → penalty = 100.5 → score = 0 (hard floor)

### Sliding Window N-Gram Matcher

```python
# Finds multi-word phrases in O(n) time
phrase_tokens = normalize(keyword_phrase)   # e.g. ["san", "jose", "bakery"]
window_size   = len(phrase_tokens)          # 3

for i in range(len(tokens) - window_size + 1):
    if tokens[i : i + window_size] == phrase_tokens:
        match_positions.append(i)

density = (len(match_positions) / len(tokens)) * 100
```

### RFM Customer Scoring

```python
# Each dimension scored 1–3 using quantile bins
R_Score = 3 if bought recently, 1 if long ago
F_Score = 3 if frequent buyer, 1 if rare
M_Score = 3 if high spender,   1 if low

RFM_Score = R + F + M   # range 3–9
# Champion=8–9 | Loyal=6–7 | Potential=4–5 | At Risk=3
```

### Market Basket (Combo Logic)

```python
# For every order with 2+ items, count product pair co-occurrences
Support(A,B)     = orders_with_both / total_orders
Confidence(A→B)  = Support(A,B) / Support(A)
Lift(A,B)        = Confidence(A→B) / Support(B)
# Lift > 1 = genuine association (not just popular products)
# Scalability: 25 SKUs → 300 pairs (direct). 500+ SKUs → use FP-Growth
```

---

## Data Sources

| Dataset | Source | Currency | Used For |
|---|---|---|---|
| Olist Brazilian E-Commerce | [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | BRL → USD (×0.20) | E-Commerce store type |
| UCI Online Retail II | [Kaggle](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci) | GBP → USD (×1.27) | Brick-and-Mortar store type |
| Mock data (fallback) | `generate_mock_data.py` | USD | Development / demo |

---

## Resampling Rules

| Rule | Trigger | Action |
|---|---|---|
| R-01 | Negative quantity | DROP — returns excluded from sales |
| R-02 | Null price | FILL with category median |
| R-03 | Null date | DROP — can't place on time axis |
| R-04 | Missing day in series | FILL with $0 via `.resample("D").sum().fillna(0)` |
| R-05 | Currency | BRL×0.20 → USD · GBP×1.27 → USD |
| R-06 | Duplicate TXN+Product | DROP duplicate, keep first |

---

## Chaos Monkey — Anomaly Injection

7 real-world data quality failures injected at 2% rate, all verified as cleaned:

| Code | Anomaly | Real-World Cause |
|---|---|---|
| A1 | `Current_Stock = -5` | Scanner logged return before original sale |
| A2 | `Retail_Price = NaN` | CSV column misalignment on import |
| A3 | `Retail_Price < Cost_Price` | Manual markdown set below cost |
| A4 | Future `Last_Sold_Date` | POS terminal clock drift |
| A5 | `Current_Stock = 99999` | ERP migration defaulted to max integer |
| A6 | Duplicate rows | ETL cron job ran twice |
| A7 | Blank `Product_Name` | Operator skipped required field |

---

## Forecasting Tiers

| Tier | Model | Status |
|---|---|---|
| 1 | SMA · EMA · Holt-Winters | ✅ Live |
| 2 | XGBoost with lag + cyclic features | 📋 Week 9 |
| 3 | SARIMAX with exogenous inputs (FX rate, events) | 📋 Future scope |

---

## Week Progress

| Week | Phase | Status |
|---|---|---|
| 1–3 | Concept, Charter, Scope | ✅ Done |
| 4–6 | Data Schema & Source | ✅ Done |
| 7–9 | Back-end Algorithm Engineering | 🔄 In Progress |
| 9–11 | Front-end Dashboard | 📋 Planned |
| 12–14 | System Optimisation | 📋 Planned |
| 14+ | Final Demo Prep | 📋 Planned |

---

*Built with Python · Streamlit · Pandas · Plotly · Statsmodels*
