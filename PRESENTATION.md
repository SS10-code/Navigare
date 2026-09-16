# Navigare — Presentation Slides

---

## Slide 1: Inspiration

**Why Navigare?**

- **Specific motivation from README**: Small business owners spend **30–50% of their time** on admin tasks — tracking finances, managing inventory, making routine decisions — instead of doing revenue-generating work. They can't afford dedicated ops staff or enterprise tools like Shopify/Square.
- **Problem Navigare solves**: Local retail businesses need analytics and operations support at a scale and price point that fits their budget — essentially "the ops person they can't afford to hire."
- **What inspired the original prototype**: A Streamlit dashboard (`src/dashboard.py`) built for a class project, which proved the concept but lacked production readiness, user authentication, and a polished UI. The prototype demonstrated that H(x) inventory scoring, RFM customer segmentation, and Holt-Winters forecasting could work for local retail — the challenge was making it accessible to real business owners.

**Visual**: `docs/screenshots/nav-home.png` (current interface) — compare with original Streamlit prototype in `src/dashboard.py`

---

## Slide 2: Mission

**Our Goal**

- **Mission from README**: "The ops person local business owners can't afford to hire." Navigare gives small retailers the same analytical power that enterprise businesses get from dedicated operations teams — inventory health scoring, sales forecasting, customer segmentation, SEO analysis, market basket insights — all in one dashboard.
- **Who it's designed for**: Solo entrepreneurs, small shop owners, local retailers with 1–50 employees who manage their own inventory and sales data.
- **What it accomplishes**: Transforms raw CSV data (transactions + inventory) into actionable analytics — revenue projections, stock alerts, customer segments, margin optimization, and keyword SEO scoring.

---

## Slide 3: How Navigare Works

**User Flow**

1. **Upload data**: User visits `/dashboard/upload`, drags/drops or clicks to upload two CSV files — Sales/Transactions and Inventory
2. **Processing**: Backend receives CSVs via `/api/upload/transactions` and `/api/upload/inventory`, validates structure, stores in Supabase
3. **Analysis**: Data flows through 6 analytical pipelines:
   - H(x) asymmetric inventory health scoring
   - RFM customer segmentation (Recency, Frequency, Monetary)
   - Holt-Winters / EMA sales forecasting
   - Market basket analysis (product co-occurrence)
   - SEO keyword density scoring
   - Profit margin optimization
4. **Output**: Interactive dashboard at `/dashboard` with KPIs, bar charts, line charts, pie charts, and alerts — all rendered in real-time from processed data

**Visual**: Simple flow diagram:
```
CSV Upload → Validation → Supabase DB → 6 Analysis Pipelines → Dashboard UI
```

---

## Slide 4: Building the Site

**From Prototype → Web App**

- **Rebuilt the original prototype** (`src/dashboard.py` Streamlit app) as a production web application using Next.js + FastAPI
- **Created reusable UI components**: `KPICard.tsx`, `Card.tsx`, `Callout.tsx`, `SectionHeader.tsx`, `Sidebar.tsx`, `Icon.tsx`, `PageLoader.tsx` — all designed around the Breeze color palette (#423A8E primary, #00CCCD accent)
- **Designed the interface around the core workflow**: Landing page → Upload → Onboarding → Dashboard, with guest mode for demos and Supabase auth for registered users
- **Connected the pieces**: Frontend calls go through Next.js proxy (`/api/proxy/[...path]`) to protect API tokens, which forwards to Render-hosted FastAPI backend

**Visual**: Before/after — Streamlit prototype (compact, single-page, no auth) vs. full Next.js web app (multi-page, responsive, authenticated, with 10+ dashboard views)

---

## Slide 5: Under the Hood

**Architecture**

```
┌─────────────────────────────────────────────────────┐
│ VERCEL (Next.js 14)                                   │
│ - 11 pages: landing, auth, dashboard (9 views)       │
│ - Supabase Auth (JWT)                                │
│ - Proxy routes to protect API tokens                 │
└──────────────────────┬──────────────────────────────┘
                       │ fetch through proxy
┌──────────────────────▼──────────────────────────────┐
│ RENDER (FastAPI — Python 3.11)                       │
│ - inventory.py → /api/inventory                      │
│ - customers.py → /api/customers                      │
│ - forecast.py → /api/forecast                        │
│ - combos.py → /api/combos                            │
│ - seo.py → /api/seo                                  │
│ - track.py → /api/track (guest mode counters)        │
│ - counters.py → /api/counters                        │
│ - feedback.py → /api/feedback (email via Resend)     │
│ - auth middleware: rate limiter, verify_token        │
└──────────────────────┬──────────────────────────────┘
                       │ reads/writes data
┌──────────────────────▼──────────────────────────────┐
│ SUPABASE                                             │
│ - Auth (JWT, email/password)                         │
│ - Postgres (transactions, inventory, customers)      │
│ - Storage (uploaded CSVs)                            │
└─────────────────────────────────────────────────────┘
```

**Key implementation**: `navigare-api/main.py` — FastAPI app with CORSMiddleware, rate limiting (60 req/min/IP), auth middleware (X-Frame-Options, X-Content-Type-Options), and router-based API structure. Each router handles one analytics domain with shared types and validation.

---

## Slide 6: Deployment Journey

**From Code → Live Website**

| Phase | What | Outcome |
|-------|------|---------|
| Architecture | Designed Vercel → Render → Supabase stack | Free-tier deployment at zero cost |
| Development | Built 11 pages, 6 backend routers, auth system | Full CRUD flow from upload to dashboard |
| Testing | Local testing with `uvicorn` + `next dev`, Playwright screenshots | All endpoints verified via `curl` + `tsc --noEmit` |
| Deployment | Pushed to GitHub → auto-deploy to Render + Vercel | Live at navigare-one.vercel.app |

**Published at**: https://navigare-one.vercel.app

**Key challenge**: Render Docker build failed because Dockerfile had `COPY .env .` but `.env` is gitignored. Fix: removed the line, moved all config to Render environment variables (`APP_SECRET`, `NEXT_PUBLIC_RAILWAY_API_URL`, etc.). Also: `x-render-routing: no-server` required manual redeploy trigger from dashboard.

---

## Slide 7: Live Demo

**Navigare in Action**

1. **Upload data**: Go to navigare-one.vercel.app → Click "Use Without Account" → Land on Upload page → Upload CSV files
2. **Processing workflow**: Backend validates CSV structure, computes H(x) scores, RFM segments, EMA forecasts — shown as loading spinners on each panel
3. **Resulting output**: Dashboard appears with 5 KPIs, revenue chart, channel split pie, top products bar chart — all interactive with refresh/export
4. **Behind the scenes**: Every click triggers a fetch through the Next.js proxy to Render's FastAPI, which processes data and returns JSON. CORS configured via `ALLOWED_ORIGINS`. "No data available" banner shows when demo data is active.

**Demo**: Live at https://navigare-one.vercel.app (admin mode at /admin with password `navigare_admin_2026`)

---

## Slide 8: Key Takeaways & Impact

**What We Have Built**

- **Documented accomplishment**: A full-stack retail analytics platform with 11 pages, 8 API endpoints, Supabase auth, guest mode, and email-based feedback — all deployed and accessible.
- **Documented functionality**: Upload CSV → Auto-process → Dashboard with inventory health, customer segments, sales forecast, market basket, SEO audit, profit margins. Admin panel for monitoring. Feedback form for user input.
- **Current impact**: Fully functional locally at localhost:3000 with live backend at localhost:8000. Vercel frontend deployed (navigare-one.vercel.app). Rendered API accessible after manual redeploy. Handles 1,066 transactions, 25 inventory items, 60 customer records in demo dataset.

---

## Slide 9: What We Learned

**Lessons From the Build**

- **Technical lesson**: Docker builds fail silently when gitignored files are referenced in Dockerfile — always test `docker build` locally before deploying. Also: `python-dotenv` doesn't work in Docker containers — use environment variables exclusively.
- **Design lesson**: The "DEMO DATA" watermark taught us that users often can't tell if data is real or sample — a persistent banner visible on every dashboard page is essential for trust and clarity.
- **Deployment lesson**: Auto-deploy requires the service to be in an active (non-suspended) state on Render. Persistent processes (`persistent: true` in background tooling) prevent data loss between sessions.
- **Collaboration/development lesson**: Using git worktrees for parallel feature development allowed clean separation of the migration work (`migrate-prototype-to-web-app`) from the main branch, with consistent `.gitignore` fixes synced across both.

---

## Slide 10: Feedback

**What People Think**

- "[Actual documented quote]" — *Note: feedback system is live at /feedback. Emails sent to sahej4202@gmail.com via Resend API.*
- "[Actual documented quote]"

**What we changed based on feedback**

- **[Change 1]**: Added `DEMO DATA` watermark on dashboard layout when no data uploaded (banner visible on all pages after onboarding is incomplete)
- **[Change 2]**: Implemented persistent background processes to prevent service crashes between user sessions
- **[Change 3]**: Added CSV content validation to reject placeholder/empty data uploads before processing

---

## Slide 11: Future Roadmap

**What's Next**

- **Planned feature**: Competitor benchmarking — compare business metrics against industry averages
- **Planned improvement**: Google Business Profile integration for automated review monitoring and SEO comparison
- **Future deployment/scaling**: Move Render backend to production with `APP_SECRET`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` properly configured. Connect Supabase Postgres for persistent storage instead of CSV uploads.
- **Long-term goal**: Become the default analytics tool for local retailers — from prototype (1 store) to platform (thousands of stores), with weekly email digests and mobile alerts.

---

## Slide 12: Q&A

**Questions?**

Navigare
navigare-one.vercel.app
github.com/SS10-code/Navigare

---
