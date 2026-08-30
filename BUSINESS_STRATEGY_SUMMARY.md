# Navigare — Retail Data Insights Summary

## Overview
Analysis of prototype retail dataset: **1,066 transactions**, **25 inventory items**, **60 customers** across 5 countries.

---

## Transaction Volume & Revenue

| Metric | Value |
|--------|-------|
| Total transactions | 1,066 |
| Total revenue (USD) | $95,352 |
| Top category (revenue) | Electronics (1,05) — $8,405 |
| Second category | Home Utilities — $10,520 |
| Third category | Sports — $9,977 |
| Fastest-selling product | SC00005 — 20 units |

### Revenue by Top 5 Categories
1. **Home Utilities**: $10,520 (11.0%)
2. **Sports**: $9,977 (10.5%)
3. **Fashion**: $9,512 (9.9%)
4. **Food**: $6,749 (7.1%)
5. **Electronics**: $8,405 (8.8%)

---

## Operational Timing — Peak Hours

| Hour | Transactions | Notes |
|------|-------------|-------|
| 08:00 | 80 | Morning rush |
| 09:00 | 113 | **Peak start** |
| 12:00 | 98 | Lunch hour |
| 13:00 | 107 | Afternoon rush |
| 14:00 | 96 | Continued traffic |
| 15:00 | 103 | Pre-close peak |
| 16:00 | 106 | **Peak end** |
| 17:00+ | declining | Evening wind-down |

**Insight**: Peak window is 09:00–16:00 (8 hours). Push notifications / email campaigns should target **08:30**, **12:30**, **16:00** for maximum engagement.

---

## Inventory Status

| Metric | Value |
|--------|-------|
| Total products | 25 |
| Low-stock items | 13 (52%) |
| Dead stock items | 4 (16%) |
| Average margin | 67.5% |

### Key Inventory Concerns
- **52% of inventory is low-stock** — reorder alerts should fire at current thresholds
- **4 dead-stock items** (e.g., Cinnamon Roll — 38 days since last sale) — consider markdowns or discontinuation
- **Top margin opportunity**: Croissant (65.7% margin, 13 units in stock) — high turnover potential

### Data Quality Issues Found (from chaos_report)
7 injection types detected in raw data, all cleaned:
1. **Negative stock** (row 23) — scanner posted before original sale
2. **Null prices** (row 12) — CSV column misalignment
3. **Price inversions** (row 18) — manual markdown set retail below cost
4. **Future dates** (row 14) — POS terminal clock drift
5. **Stock outliers** (row 12) — ERP migrated with max int value
6. **Duplicate rows** (row 23) — ETL cron overlap
7. **Blank names** (row 25) — operator skipped field

**Operational insight**: Data entry bottlenecks occur during high-traffic hours (09:00–11:00). Implement input validation and a loading spinner to prevent double-submits.

---

## Customer Segments (RFM Analysis)

| Segment | Count | % |
|---------|-------|---|
| Potential | 23 | 38.3% |
| Champion | 20 | 33.3% |
| Loyal | 11 | 18.3% |
| At Risk | 6 | 10.0% |

### Customer Behavior
- **Champions** (20) and **Potential** (23) together represent 67% of base — focus retention campaigns here
- **At Risk** (6) — target with win-back offers; last purchase > 30 days
- **Loyal** (11) — stable revenue; cross-sell opportunities

---

## Forecast Snapshot (EMA, α=0.133, span=14)

| Metric | Value |
|--------|-------|
| Forecasted demand (day 1) | 358.83 |
| Forecasted demand (day 14) | 346.67 |
| Trend | **-3.4% decline** over 2 weeks |

**Insight**: Demand is slowly declining. Trigger inventory review at -5% threshold. Current forecast can power the frontend dashboard's "predicted sales" visualization.

---

## UI Bottleneck Observations

| Flow | Observation | Recommendation |
|------|------------|----------------|
| Guest mode → dashboard | Counter increments server-side, 200ms latency | Add optimistic UI update |
| Upload page | txnLoading / invLoading separate — prevents overlap | Good, but add progress % |
| Onboarding | Draft auto-saved to localStorage — prevents data loss | Add "Draft saved" indicator |
| Login | No loading state — user may click multiple times | Add spinner (anti-spam) |
| Price slider | Clamped to [2, 10] — prevents invalid input | Good |

---

## Next Actions

1. **Deploy Render backend** — Dockerfile fix committed, needs redeploy for API access
2. **Collect business owner reviews** — send X/Twitter link once API is live
3. **Add "Peak Hours" chart** to dashboard — visualize hourly transaction heatmap
4. **Add reorder alerts** on inventory page — 13 low-stock flags
5. **Weekly business summary emails** — summarize top products, peak hours, at-risk customers
6. **Referral features** — Champions + Loyal segment are likely to refer
