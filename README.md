# 🧭 Navigare — Local Retail Analytics

> **The ops person local business owners can't afford to hire.**

![Phase](https://img.shields.io/badge/Phase-Production%20Ready-423A8E?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-00CCCD?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-00CCCD?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=flat-square&logo=next.js&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3ECF8E?style=flat-square&logo=supabase&logoColor=white)

---

## 📌 Problem Statement

Small business owners spend **30–50% of their time** on admin — tracking finances, managing inventory, making routine decisions — instead of doing the work that earns revenue. They have no dedicated ops staff, no analytics tools built for their scale, and no time to learn enterprise software like Shopify or Square.

Navigare's job is to be the ops person they can't afford to hire.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│ VERCEL (Next.js / React)                            │
│ - All UI pages, charts, tables                      │
│ - Supabase Auth (login/logout)                      │
│ - File upload → Supabase Storage                    │
│ - Calls Railway API for analytics                   │
└──────────────────────┬──────────────────────────────┘
                       │ REST API calls
┌──────────────────────▼──────────────────────────────┐
│ RAILWAY (FastAPI — Python)                          │
│ - inventory_health.py → /api/inventory              │
│ - RFM logic → /api/customers                        │
│ - Holt-Winters → /api/forecast                      │
│ - Market basket → /api/combos                       │
│ - seo_engine.py → /api/seo                         │
│ - Weekly digest → /api/digest                       │
└──────────────────────┬──────────────────────────────┘
                       │ reads/writes data
┌──────────────────────▼──────────────────────────────┐
│ SUPABASE                                            │
│ - Auth (JWT, email/password)                        │
│ - Postgres (transactions, inventory, customers)      │
│ - Storage (uploaded CSVs)                           │
└─────────────────────────────────────────────────────┘
```

**Free tier stack:**
- Vercel hobby — unlimited deployments
- Render — free web service (no credit card)
- Supabase free — 500MB DB, 1GB storage, 50k MAU
- Resend free — 3,000 emails/month

> Note: Railway is no longer free. Use Render instead — it requires no credit card and supports Docker.

---

## 🚀 Quick Start

### Option A: Run the Streamlit Prototype (local)

```bash
# Clone the repo
git clone https://github.com/SS10-code/Navigare.git
cd Navigare/src

# Install dependencies
pip install -r requirements.txt

# Run in order
python generate_mock_data.py    # Seed raw data
python business_metrics.py      # Compute metrics
streamlit run dashboard.py      # Launch dashboard
```

Default password: `navigare2025`

### Option B: Deploy the Production Stack

#### 1. Supabase Setup
1. Create a project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run `supabase-schema.sql`
3. Enable Email auth in Authentication → Providers
4. Copy your project URL and anon key

#### 2. Render Backend (free, no credit card)
1. Create a project at [render.com](https://render.com)
2. Connect your GitHub repo
3. Select `navigare-api/` as the root directory
4. Render auto-detects the Dockerfile
5. Add environment variables:
   - `APP_SECRET` — shared secret for API auth
   - `SUPABASE_URL` — from Supabase
   - `SUPABASE_SERVICE_KEY` — from Supabase (Settings → API)
   - `RESEND_API_KEY` — from resend.com (optional, for digests)
6. Deploy — your API will be at `https://navigare-api.onrender.com`

#### 3. Vercel Frontend
1. Create a project at [vercel.com](https://vercel.com)
2. Connect your GitHub repo
3. Select `navigare-web/` as the root directory
4. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_RAILWAY_API_URL` — use your Render URL
5. Deploy

---

## 📁 Project Structure

```
Navigare/
├── src/                                    # Streamlit prototype
│   ├── dashboard.py                        # 8-page app (v6, Phase 4)
│   ├── requirements.txt
│   ├── config.toml
│   ├── inventory_health.py                 # H(x) asymmetric scoring
│   ├── business_metrics.py                 # MAD, ROP, RFM, Market Basket
│   ├── feature_engineering.py              # EMA, Z-Score, lags, VIF, ADF
│   ├── seo_engine.py                       # N-gram keyword density
│   ├── chaos_monkey.py                     # Anomaly injection + cleaning
│   ├── generate_mock_data.py               # Data seeder
│   └── schema_mapper.py                    # Olist + UCI → unified USD
│
├── navigare-api/                           # FastAPI backend (Render)
│   ├── main.py                             # CORS, auth, routing
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── inventory.py                    # POST /api/inventory
│   │   ├── customers.py                    # POST /api/customers
│   │   ├── forecast.py                     # POST /api/forecast
│   │   ├── combos.py                       # POST /api/combos
│   │   ├── seo.py                          # POST /api/seo
│   │   └── digest.py                       # POST /api/digest
│   ├── inventory_health.py                 # Copied from src/
│   ├── business_metrics.py                 # Copied from src/
│   ├── seo_engine.py                       # Copied from src/
│   ├── feature_engineering.py              # Copied from src/
│   └── ...
│
├── navigare-web/                           # Next.js frontend (Vercel)
│   ├── app/
│   │   ├── layout.tsx                      # Root layout
│   │   ├── page.tsx                        # Landing page
│   │   ├── auth/login/page.tsx             # Supabase login
│   │   └── dashboard/
│   │       ├── layout.tsx                  # Protected sidebar
│   │       ├── page.tsx                    # Overview
│   │       ├── inventory/page.tsx          # Inventory Health
│   │       ├── customers/page.tsx          # RFM Segments
│   │       ├── combos/page.tsx             # Market Basket
│   │       ├── forecast/page.tsx           # Sales Forecast
│   │       ├── seo/page.tsx                # SEO Auditor
│   │       ├── upload/page.tsx             # CSV Upload
│   │       ├── profit/page.tsx             # Margin Optimizer
│   │       ├── onboarding/page.tsx         # 4-step wizard
│   │       └── digest/page.tsx             # Email setup
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── KPICard.tsx
│   │   └── ...
│   ├── lib/
│   │   ├── supabase/client.ts
│   │   ├── supabase/server.ts
│   │   └── api.ts
│   ├── package.json
│   └── tailwind.config.ts
│
└── supabase-schema.sql                     # Database schema
```

---

## 📊 Features

| Feature | Streamlit | Production API | Production UI |
|---|---|---|---|
| Revenue Dashboard | ✅ Live | ✅ /api/forecast | ✅ |
| Inventory Health H(x) | ✅ Live | ✅ /api/inventory | ✅ |
| Market Basket Analysis | ✅ Live | ✅ /api/combos | ✅ |
| Customer RFM Segments | ✅ Live | ✅ /api/customers | ✅ |
| Sales Forecast (HW) | ✅ Live | ✅ /api/forecast | ✅ |
| SEO Auditor | ✅ Live | ✅ /api/seo | ✅ |
| Feature Engineering | ✅ Live | ✅ | ✅ |
| Upload Data | ✅ Fixed | ✅ | ✅ |
| Login Screen | ✅ Fixed | ✅ Supabase Auth | ✅ |
| Profit Margin Optimizer | ✅ New | 🔄 Planned | ✅ |
| Onboarding Flow | ✅ New | 🔄 Planned | ✅ |
| Weekly Email Digest | ✅ API | ✅ /api/digest | ✅ |
| Mobile Alerts | 🔄 CSS tweaks | 🔄 | 🔄 |

---

## 🔑 Environment Variables

### Vercel (`navigare-web/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_RAILWAY_API_URL=https://navigare-api.onrender.com
```

### Render (`navigare-api/.env`)
```
APP_SECRET=your-api-secret
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
RESEND_API_KEY=re_...
PORT=8000
```

---

## 🧮 Key Algorithms

### H(x) Asymmetric Inventory Health
```python
# Row-wise per SKU. Score 0-100. Steep penalty near zero.
mu = (1/N) * sum(H(xi))   # Store Wellness Index
M_i = 1 if status in {CRISIS, CRITICAL, LOW} else 0  # Boolean Mask
```

### MAD → Safety Stock → ROP
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

## 🎨 Color System (Breeze Palette)

| Role | Hex | Usage |
|---|---|---|
| Primary Purple | #423A8E | Sidebar, headers |
| Primary Teal | #00CCCD | Accents, highlights |
| Amber | #FFC107 | Warnings, low stock |
| Red | #DC3545 | Crisis alerts |
| Green | #198754 | Healthy states |
| Blue | #0D6EFD | Info states |

---

## 📈 Roadmap

| Week | Milestone | Status |
|---|---|---|
| 1–2 | Fix Streamlit bugs (login, upload) | ✅ Done |
| 2–4 | FastAPI backend + Next.js frontend | ✅ Done |
| 3–4 | Migrate pages one by one | ✅ Done |
| 5 | Onboarding + Profit Optimizer + Email Digest | ✅ Done |
| 6 | Polish, landing page, deploy | 🔄 In Progress |
| 7+ | Competitor benchmarking, GBP integration | Planned |

---

## 🤝 Contributing

This is a portfolio project. For issues or feature requests, open a GitHub issue.

---

*Built with Python, Streamlit, FastAPI, Next.js, Supabase*
*github.com/SS10-code/Navigare*
