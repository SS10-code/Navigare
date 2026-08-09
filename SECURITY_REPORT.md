# Security & Deployment Audit Report

**Project:** Navigare — Local Retail Analytics
**Date:** 2026-08-08
**Scope:** Full repo review before public GitHub push + deployment verification

---

## 1. Secrets Scan — Result: PASS ✅

| Check | Result |
|---|---|
| API keys / tokens / passwords in source code | None found |
| Secrets in git history (`git log --all`, full diff scan) | None found |
| `.env` / key / cert / credential files | None present |
| Firebase credentials (README lists Firebase as *future*) | None present |
| Hardcoded URLs with embedded credentials | None found |

**Conclusion:** No API keys or secrets are present in code, config, data, or history. The repo is safe to publish as-is.

---

## 2. Data Privacy — Result: PASS ✅

All datasets are **synthetic mock data** generated with Faker / simulated pipelines:

- `customers.csv` — fictional names + `@example.org` / `@example.com` emails (reserved domains)
- `transactions.csv`, `inventory.csv` — generated fake sales/inventory
- `src/data/synthetic/` — simulated Olist (BRL) and UCI (GBP) samples

**No real customer PII, no real business data, no payment data.**

---

## 3. Deployed-App Security — Result: FIXED ⚠️ → ✅

| Issue | Severity | Status |
|---|---|---|
| `config.toml` had `enableXsrfProtection = false` | Medium | **Fixed** — now `true` |
| `config.toml` had `enableCORS = false` | Medium | **Fixed** — now `true` |
| `unsafe_allow_html=True` usage in dashboard | Low | Acceptable — HTML is static formatting; SEO explanations are numeric-only; user keywords render through Streamlit's escaping |

---

## 4. Repository Hygiene — Result: FIXED ⚠️ → ✅

| Issue | Status |
|---|---|
| `src/__pycache__/*.pyc` bytecode was tracked in git | **Fixed** — untracked and removed |
| No `.gitignore` (`.pyc`, `.env`, secrets could be committed accidentally) | **Fixed** — `.gitignore` added |
| No `requirements.txt` (blocked Vercel/Render deployment) | **Fixed** — pinned versions added |

---

## 5. Deployment Verification — Result: PASS ✅

Tested with the exact dependency set in `requirements.txt` (Python 3.11):

| Test | Result |
|---|---|
| Syntax check on all 8 source modules (`py_compile`) | PASS |
| Full data pipeline (`generate_mock_data` → `schema_mapper` → `chaos_monkey` → `feature_engineering` → `business_metrics` → `inventory_health`) | PASS — all stages complete, chaos test: 25 → 26 → 25 |
| Streamlit app headless smoke test — all 8 pages (Overview, Inventory, Combo, Customers, Forecast, SEO, Under the Hood, Glossary) | PASS — no errors, no exceptions |

---

## 6. Deployment Notes (for Vercel/Render)

1. **Working directory:** `dashboard.py` loads data via CWD-relative paths (`data/...`). Run from the repo root: `streamlit run src/dashboard.py`.
2. **Static data:** commit `data/` so the deployed app has CSVs available; the pipeline does not auto-run on the server.
3. **Runtime command:** `streamlit run src/dashboard.py --server.port $PORT --server.address 0.0.0.0`
4. **Python version:** 3.11 recommended (3.10+ supported).
5. `config.toml` is already located under `src/` so Streamlit picks it up when launching `src/dashboard.py`.

---

## 7. What Goes Public vs Stays Local

| Goes public (committed) | Stays local (never committed) |
|---|---|
| Source code (`src/*.py`) | API keys, passwords, tokens (none exist) |
| Mock/synthetic data (`data/`, `src/data/`) | Real customer data (none exists) |
| `requirements.txt`, `config.toml`, `.gitignore` | `.env` files (ignored via `.gitignore`) |
| `README.md`, screenshots in `assets/` | `__pycache__/` bytecode (now ignored) |
| This report | Any future real business data |
