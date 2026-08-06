# 🧭 Navigare — Local Retail Analytics

> **Empowering small business owners to spend less time on admin and more time growing their business.**

![Phase](https://img.shields.io/badge/Phase-4%20Frontend-423A8E?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-00CCCD?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

---

## 📌 Problem Statement

Small business owners spend **30–50% of their time** on administrative operations — tracking finances, managing paperwork, organizing inventory, and making routine operational decisions — rather than focusing on their craft.

Without access to simple analytics tools, many owners are forced to **manage their stores blindly**. Lacking actionable insights, these small businesses face disproportionately high closure rates, threatening local economic independence.

---

## 💡 Solution & Impact

### Immediate Impact
- **Unified Business Dashboard** — real-time visibility into sales, expenses, and key metrics
- **Data-Driven Inventory** — MAD, Safety Stock, and Reorder Point calculations per SKU
- **SEO Auditor** — instant local search optimisation feedback on any web copy

### Future Impact
- **Predictive Forecasting** — XGBoost demand forecasting before shortages happen
- **Automated Local SEO** — algorithmic suggestions to maximise local search visibility
- **Profitability Engine** — waste reduction and margin optimisation

---

## Features

| Feature | Status | Description |
|---|---|---|
| Business Overview | Live | Revenue, orders, AOV, channel split, top products |
| Inventory Health H(x) | Live | Asymmetric health score per SKU, wellness index, priority alerts |
| Reorder Alerts | Live | MAD + Safety Stock + ROP + boolean mask dispatch |
| Market Basket | Live | Support, Confidence, Lift for product pair recommendations |
| Customer Segments | Live | RFM scoring — Champion to At Risk |
| Sales Forecast | Live | SMA + EMA + Holt-Winters with 14-day projection |
| SEO Auditor | Live | Text normalisation, sliding window N-gram, piecewise scoring |
| Feature Engineering | Live | Z-Score, cyclic encoding, lag features, VIF, ADF stationarity |
| Glossary | Live | 30-term plain-English reference, searchable |
| Chaos Monkey | Live | 7 anomaly types at 2%, pipeline resilience verified |
| RAM Caching Layer | Live | @st.cache_data — disk I/O once, sidebar flush button |
| Filter Isolation | Live | Store and date filter flows through all derived metrics |
| XGBoost Forecasting | Planned Week 9+ | Tabular feature transformer |
| Firebase Auth | Future | Multi-user account tracking |
| Vercel Deployment | In Progress | Frontend hosted on Vercel |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (Python) migrating to Vercel |
| Backend | Python 3.10+ |
| Analytics | Pandas, NumPy, Statsmodels, Plotly |
| Database | CSV-based flat file storage |
| Forecasting | Holt-Winters (Tier 1), XGBoost (Tier 2, upcoming) |
| SEO Engine | Rule-based: regex normalisation + sliding window N-gram |
| Caching | @st.cache_data RAM layer |

---

## Getting Started

```bash
pip install streamlit pandas numpy faker statsmodels plotly
git clone https://github.com/SS10-code/Navigare.git
cd Navigare
```

Run in order:
```bash
python generate_mock_data.py    # 1. Seed raw data
python schema_mapper.py         # 2. Merge Olist BRL + UCI GBP to USD
python chaos_monkey.py          # 3. Test pipeline resilience
python feature_engineering.py   # 4. Build feature matrix
python business_metrics.py      # 5. Compute all business metrics
streamlit run dashboard.py      # 6. Launch dashboard
```

---

## File Structure

```
Navigare/
├── dashboard.py              Streamlit app (8 pages, Breeze color scheme)
├── generate_mock_data.py     Seeds raw CSV files
├── schema_mapper.py          Merges Olist + UCI into unified USD schema
├── chaos_monkey.py           7 anomaly injection types, resilience test
├── feature_engineering.py    EMA, Z-Score, cyclic encoding, lags, VIF, ADF
├── business_metrics.py       MAD, Safety Stock, ROP, RFM, Market Basket
├── inventory_health.py       H(x), wellness index mu, boolean mask M
├── seo_engine.py             Text normalisation, N-gram, piecewise scoring
│
└── data/
    ├── raw/                  inventory.csv, transactions.csv, customers.csv
    └── clean/                unified_transactions.csv, features.csv,
                              inventory_metrics.csv, customer_rfm.csv,
                              combo_pairs.csv, ema_forecast.csv, ...
```

---

## Key Algorithms

### H(x) Asymmetric Inventory Health
```python
# Row-wise per SKU. Score 0-100. Steep left side (stockout >> overstock cost)
mu = (1/N) * sum(H(xi))   # Store Wellness Index
M_i = 1 if status in {CRISIS, CRITICAL, LOW} else 0  # Boolean Mask
```

### MAD to Safety Stock to ROP
```python
MAD          = mean(|daily_demand - avg_demand|)
Safety_Stock = Z * MAD * sqrt(Lead_Time)    # Z=1.65 for 95% service level
ROP          = (Avg_Daily_Demand * Lead_Time) + Safety_Stock
```

### SEO Piecewise Scoring
```python
if   density < 1.0%:   score = 50                               # Under-optimized
elif density <= 3.5%:  score = 100                              # Sweet spot
else:                  score = max(0, int(100 - (excess * 15))) # Stuffing penalty
```

---

## Color System (Breeze Palette)

| Role | Hex | Usage |
|---|---|---|
| Primary Purple | #423A8E | Sidebar, headers |
| Primary Teal | #00CCCD | Accents, highlights |
| Amber | #FFC107 | Warnings, low stock |
| Red | #DC3545 | Crisis alerts |
| Green | #198754 | Healthy states |
| Blue | #0D6EFD | Info states |

---

## Data Sources

| Dataset | Source | Currency |
|---|---|---|
| Olist Brazilian E-Commerce | kaggle.com/datasets/olistbr/brazilian-ecommerce | BRL x 0.20 = USD |
| UCI Online Retail II | kaggle.com/datasets/mashlyn/online-retail-ii-uci | GBP x 1.27 = USD |

---

## Project Timeline

| Weeks | Phase | Status |
|---|---|---|
| 1-3 | Concept, Charter, Scope | Complete |
| 4-6 | Data Schema & Source | Complete |
| 7-9 | Back-end Algorithm Engineering | Complete |
| 9-11 | Front-end Dashboard | In Progress |
| 12-14 | System Optimisation | Planned |
| 14-15 | Final Demo Prep | Planned |
| 16 | Presentation & Impact | Planned |

---

*Built with Python, Streamlit, Pandas, Plotly, Statsmodels*
*github.com/SS10-code/Navigare*
