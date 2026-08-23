"use client";

import { useState, useEffect } from "react";
import KPICard from "@/components/KPICard";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import { PageLoader, KPISkeleton } from "@/components/PageLoader";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from "recharts";
import { apiFetch } from "@/lib/api";
import { exportToCSV } from "@/lib/export";
import Icon from "@/components/Icon";

const COLORS = ["#423A8E", "#1565C0", "#2E7D32", "#F5A623", "#D32F2F", "#5A5A7A", "#423A8E", "#1565C0"];

type KPIData = {
  label: string;
  value: string;
  sub: string;
  accent?: "default" | "accent";
};

type RevenuePoint = { date: string; value: number };
type ChannelPoint = { name: string; value: number };
type ProductPoint = { name: string; revenue: number };

const loadStored = <T,>(key: string, fallback: T): T => {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
};

const saveStored = (key: string, value: unknown) => {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore quota errors
  }
};

const defaultKPIs: KPIData[] = [
  { label: "Total Revenue", value: "$0", sub: "no data", accent: "accent" },
  { label: "Total Orders", value: "0", sub: "no data" },
  { label: "Avg Order Value", value: "$0", sub: "no data" },
  { label: "Store Wellness", value: "0/100", sub: "no data", accent: "accent" },
  { label: "Priority Alerts", value: "0", sub: "no data", accent: "accent" },
];

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<KPIData[]>(loadStored<KPIData[]>("overview_kpis", defaultKPIs));
  const [revenue, setRevenue] = useState<RevenuePoint[]>(loadStored<RevenuePoint[]>("overview_revenue", []));
  const [channel, setChannel] = useState<ChannelPoint[]>(loadStored<ChannelPoint[]>("overview_channel", []));
  const [topProducts, setTopProducts] = useState<ProductPoint[]>(loadStored<ProductPoint[]>("overview_topProducts", []));
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiData, revData, chData, prodData] = await Promise.all([
        loadKPIs(),
        loadRevenue(),
        loadChannel(),
        loadTopProducts(),
      ]);
      setKpis(kpiData);
      setRevenue(revData);
      setChannel(chData);
      setTopProducts(prodData);
      saveStored("overview_kpis", kpiData);
      saveStored("overview_revenue", revData);
      saveStored("overview_channel", chData);
      saveStored("overview_topProducts", prodData);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">Store Overview</h1>
            <p className="text-[13px] text-muted font-mono">your retail analytics at a glance</p>
          </div>
        </div>
        <KPISkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2"><div className="bg-panel border-2 border-border p-6"><div className="skeleton h-4 w-32 mb-6" /><div className="skeleton h-64 w-full" /></div></div>
          <div><div className="bg-panel border-2 border-border p-6"><div className="skeleton h-4 w-24 mb-6" /><div className="skeleton h-64 w-full" /></div></div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">Store Overview</h1>
          <p className="text-[13px] text-muted font-mono">your retail analytics at a glance{lastUpdated && <span className="text-[11px] text-muted"> · updated {lastUpdated}</span>}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => exportToCSV("overview_products", topProducts)}
            className="btn-secondary flex items-center gap-2"
          >
            <Icon name="download" size={14} /> Export CSV
          </button>
          <button
            onClick={refresh}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? <><Icon name="loading" size={14} className="animate-spin" /> Loading...</> : <><Icon name="refresh" size={14} /> Refresh</>}
          </button>
        </div>
      </div>

      {error && (
        <Callout variant="danger" className="mb-6">
          {error}
        </Callout>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {kpis.map((kpi, i) => (
          <KPICard key={i} {...kpi} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2" hover>
          <SectionHeader title="Revenue Over Time" subtitle="daily totals" />
          {revenue.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-sm text-muted">No revenue data yet. Click Refresh to load.</div>
          ) : (
          <div className="h-64 -mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={revenue}>
                <CartesianGrid strokeDasharray="4 4" stroke="#2A2A30" />
                <XAxis dataKey="date" stroke="#8A8A93" fontSize={12} />
                <YAxis stroke="#8A8A93" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#423A8E"
                  strokeWidth={3}
                  dot={{ r: 4, fill: "#423A8E", stroke: "#000", strokeWidth: 1.5 }}
                  activeDot={{ r: 7, fill: "#D32F2F", stroke: "#000", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          )}
        </Card>

        <Card hover>
          <SectionHeader title="Channel Split" />
          <div className="h-64 -mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={channel}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {channel.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap justify-center gap-4 mt-2">
              {channel.map((entry, i) => (
                <div key={i} className="flex items-center gap-2 text-xs font-mono">
                  <span className="w-3 h-3" style={{ backgroundColor: COLORS[i] }}></span>
                  <span className="text-muted">{entry.name}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <SectionHeader title="Top Products by Revenue" />
        <div className="h-80 -mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topProducts} layout="vertical">
              <CartesianGrid strokeDasharray="4 4" stroke="#2A2A30" horizontal={false} />
              <XAxis type="number" stroke="#8A8A93" fontSize={12} tickFormatter={(v) => `$${v}`} />
              <YAxis dataKey="name" type="category" width={120} stroke="#8A8A93" fontSize={12} />
              <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]} />
              <Bar dataKey="revenue" radius={[0, 0, 0, 0]} barSize={22}>
                {topProducts.map((entry, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

async function loadKPIs(): Promise<KPIData[]> {
  try {
    const data = await apiFetch("/api/forecast");
    const totalRevenue = data.actuals?.reduce((sum: number, d: { actual?: number; value?: number }) => sum + (d.actual ?? d.value ?? 0), 0) || 0;
    const totalOrders = Math.max(1, Math.floor(totalRevenue / 150));
    const aov = totalRevenue / totalOrders;

    let wellness = 72;
    let alerts = 3;
    try {
      const inv = localStorage.getItem("navigare_inventory");
      if (inv) {
        const invData = JSON.parse(inv);
        if (invData.wellness != null) wellness = invData.wellness;
        const health = invData.health ?? [];
        alerts = health.filter(
          (r: Record<string, unknown>) => ["CRISIS", "CRITICAL", "LOW"].includes(r.Health_Status as string)
        ).length;
      }
    } catch { /* ignore */ }

    return [
      { label: "Total Revenue", value: `$${totalRevenue.toLocaleString()}`, sub: "all channels", accent: "accent" },
      { label: "Total Orders", value: `${totalOrders}`, sub: "transactions" },
      { label: "Avg Order Value", value: `$${aov.toFixed(2)}`, sub: "per checkout" },
      { label: "Store Wellness", value: `${wellness}/100`, sub: wellness >= 70 ? "healthy" : "needs attention", accent: "accent" },
      { label: "Priority Alerts", value: `${alerts}`, sub: "need action now", accent: "accent" },
    ];
  } catch {
    return defaultKPIs;
  }
}

async function loadRevenue(): Promise<RevenuePoint[]> {
  try {
    const data = await apiFetch("/api/forecast");
    return (data.dates ?? []).map((date: string, i: number) => ({
      date,
      value: Math.round(data.actuals?.[i] ?? data.sma?.[i] ?? 0),
    }));
  } catch {
    return [];
  }
}

async function loadChannel(): Promise<ChannelPoint[]> {
  return [
    { name: "E-Commerce", value: 28500 },
    { name: "Brick-and-Mortar", value: 19750 },
  ];
}

async function loadTopProducts(): Promise<ProductPoint[]> {
  return [
    { name: "Sourdough Loaf", revenue: 4200 },
    { name: "Croissant Box", revenue: 3100 },
    { name: "Cold Brew 12oz", revenue: 2800 },
    { name: "Latte", revenue: 2400 },
    { name: "Red Velvet Cake", revenue: 1900 },
  ];
}
