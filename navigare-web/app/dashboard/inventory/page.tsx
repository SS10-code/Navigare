"use client";

import { useState, useEffect, useMemo } from "react";
import KPICard from "@/components/KPICard";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import { KPISkeleton } from "@/components/PageLoader";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { apiFetch, isEmptyApiResponse } from "@/lib/api";
import { exportToCSV } from "@/lib/export";
import Icon from "@/components/Icon";

const COLORS = ["#423A8E", "#1565C0", "#2E7D32", "#F5A623", "#D32F2F", "#5A5A7A"];

const STATUS_COLORS: Record<string, string> = {
  CRISIS: "#FF3B3B",
  CRITICAL: "#FF6B00",
  LOW: "#FFB800",
  WARNING: "#B8F73C",
  HEALTHY: "#00E676",
  OPTIMAL: "#2E7D32",
  OVERSTOCK: "#F5A623",
};

type HealthRow = { name: string; score: number; status: string };

const DEMO_HEALTH: HealthRow[] = [
  { name: "Sourdough Loaf", score: 88, status: "HEALTHY" },
  { name: "Croissant", score: 45, status: "LOW" },
  { name: "Latte", score: 92, status: "OPTIMAL" },
  { name: "Baguette", score: 72, status: "HEALTHY" },
  { name: "Red Velvet", score: 20, status: "CRITICAL" },
  { name: "Cold Brew", score: 100, status: "OPTIMAL" },
  { name: "Muffin", score: 8, status: "CRISIS" },
  { name: "Espresso", score: 55, status: "WARNING" },
];

export default function InventoryPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [healthData, setHealthData] = useState<HealthRow[]>([]);
  const [wellness, setWellness] = useState(0);
  const [criticalAlerts, setCriticalAlerts] = useState<{ sku: string; status: string; score: number; stock: number; explanation: string }[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const filteredHealth = useMemo(() => {
    return healthData.filter((row) => {
      const matchesSearch = row.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesFilter = statusFilter === "ALL" || row.status === statusFilter;
      return matchesSearch && matchesFilter;
    });
  }, [healthData, searchQuery, statusFilter]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const inventoryRows = [
        { Product_ID: 1, Product_Name: "Sourdough Loaf", Current_Stock: 35, Reorder_Level: 10 },
        { Product_ID: 2, Product_Name: "Croissant", Current_Stock: 8, Reorder_Level: 10 },
        { Product_ID: 3, Product_Name: "Latte", Current_Stock: 50, Reorder_Level: 10 },
        { Product_ID: 4, Product_Name: "Baguette", Current_Stock: 22, Reorder_Level: 10 },
        { Product_ID: 5, Product_Name: "Red Velvet", Current_Stock: 3, Reorder_Level: 10 },
        { Product_ID: 6, Product_Name: "Cold Brew", Current_Stock: 75, Reorder_Level: 10 },
        { Product_ID: 7, Product_Name: "Muffin", Current_Stock: 0, Reorder_Level: 10 },
        { Product_ID: 8, Product_Name: "Espresso", Current_Stock: 18, Reorder_Level: 10 },
      ];

      const res = await apiFetch("/api/inventory", {
        method: "POST",
        body: JSON.stringify({ rows: inventoryRows }),
      });

      const health = (res.health ?? []).map((row: Record<string, unknown>) => ({
        name: (row.Product_Name as string) ?? (row.Product_ID as string) ?? "Unknown",
        score: (row.Health_Score as number) ?? 0,
        status: (row.Health_Status as string) ?? "UNKNOWN",
      }));

      setHealthData(health);
      setWellness(Math.round(res.wellness?.wellness_score ?? 0));
      setCriticalAlerts(
        (res.critical ?? []).map((row: Record<string, unknown>) => ({
          sku: (row.Product_Name as string) ?? (row.Product_ID as string) ?? "Unknown",
          status: (row.Health_Status as string) ?? "ALERT",
          score: (row.Health_Score as number) ?? 0,
          stock: (row.Current_Stock as number) ?? 0,
          explanation: (row.Health_Explanation as string) ?? "",
        }))
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load inventory data");
      setHealthData(DEMO_HEALTH);
      setWellness(72);
      setCriticalAlerts([
        { sku: "Muffin", status: "CRISIS", score: 8, stock: 0, explanation: "ZERO STOCK — sales impossible. Immediate reorder required." },
        { sku: "Red Velvet", status: "CRITICAL", score: 20, stock: 3, explanation: "3 units — hours from stockout. Expedite reorder." },
        { sku: "Croissant", status: "LOW", score: 45, stock: 8, explanation: "8 units — at or below reorder point (10). Order now." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const statusCounts = healthData.reduce<Record<string, number>>((acc, row) => {
    acc[row.status] = (acc[row.status] || 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">Inventory Health</h1>
            <p className="text-[13px] text-muted font-mono">H(x) applied to every SKU · store wellness index μ · priority alert dispatch</p>
          </div>
        </div>
        <KPISkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div><div className="bg-panel border-2 border-border p-6 skeleton h-48" /></div>
          <div className="lg:col-span-2"><div className="bg-panel border-2 border-border p-6 skeleton h-48" /></div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">Inventory Health</h1>
          <p className="text-[13px] text-muted font-mono">H(x) applied to every SKU · store wellness index μ · priority alert dispatch</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => exportToCSV("inventory_health", healthData)}
            className="btn-secondary flex items-center gap-2"
          >
            <Icon name="download" size={14} /> Export CSV
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? <><Icon name="loading" size={14} className="animate-spin" /> Loading...</> : <><Icon name="refresh" size={14} /> Refresh</>}
          </button>
        </div>
      </div>

      {error && (
        <Callout variant="danger" className="mb-6">
          {error} — showing demo data.
        </Callout>
      )}

      {healthData.length === 0 && !loading && !error && (
        <Callout variant="info" className="mb-6">
          No inventory data available. Upload your inventory CSV to populate this view.
        </Callout>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <KPICard label="Wellness Index μ" value={`${wellness}/100`} sub={wellness >= 70 ? "Store is Healthy" : "Needs attention"} accent="accent" />
        <KPICard label="SKUs Tracked" value={`${healthData.length}`} sub="products" />
        <KPICard label="Crisis + Critical" value={`${(statusCounts["CRISIS"] || 0) + (statusCounts["CRITICAL"] || 0)}`} sub="expedite now" accent="accent" />
        <KPICard label="Low Stock" value={`${statusCounts["LOW"] || 0}`} sub="order now" accent="accent" />
        <KPICard label="Healthy + Optimal" value={`${(statusCounts["HEALTHY"] || 0) + (statusCounts["OPTIMAL"] || 0)}`} sub="no action" />
      </div>

      <Callout variant="info" className="mb-6">
        <b>H(x) — Asymmetric Health Function</b><br />
        Applied row-wise to each SKU&apos;s stock count → score 0–100.
        Asymmetric because stockouts are more damaging than overstock.
        <b> Store Wellness μ = (1/N) × Σ H(xᵢ) = {wellness}/100</b> — mean across all {healthData.length} SKUs.
      </Callout>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="flex items-center justify-center" hover>
          <div className="text-center">
            <div className={`text-5xl font-extrabold mb-2 ${wellness >= 70 ? "text-green-500" : wellness >= 40 ? "text-amber-500" : "text-red-500"}`}>{wellness}</div>
            <div className="text-sm text-muted">out of 100</div>
            <div className="mt-4 w-32 h-32 mx-auto relative">
              <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke={wellness >= 70 ? "#198754" : wellness >= 40 ? "#FFC107" : "#DC3545"}
                  strokeWidth="3"
                  strokeDasharray={`${wellness}, 100`}
                />
              </svg>
            </div>
            <div className="text-xs text-muted mt-2">Wellness Gauge</div>
          </div>
        </Card>

        <Card className="lg:col-span-2" hover>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <SectionHeader title="Health Scores by SKU" className="mt-0 mb-0" />
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Search SKUs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-40"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="CRISIS">Crisis</option>
                <option value="CRITICAL">Critical</option>
                <option value="LOW">Low</option>
                <option value="WARNING">Warning</option>
                <option value="HEALTHY">Healthy</option>
                <option value="OPTIMAL">Optimal</option>
                <option value="OVERSTOCK">Overstock</option>
              </select>
            </div>
          </div>
          <div className="h-80 -mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={filteredHealth}>
                <CartesianGrid strokeDasharray="4 4" stroke="#2A2A30" />
                <XAxis dataKey="name" stroke="#8A8A93" fontSize={11} tick={{ fontSize: 11 }} />
                <YAxis stroke="#8A8A93" fontSize={12} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #E5E7EB", fontSize: 13 }}
                  formatter={(value: number, name: string, props: any) => [value, props.payload.status]}
                />
                <Bar dataKey="score" radius={[0, 0, 0, 0]}>
                  {filteredHealth.map((entry) => (
                    <Cell key={entry.name} fill={STATUS_COLORS[entry.status] || "#7C5CFF"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card hover>
        <div className="flex items-center justify-between mb-4">
          <SectionHeader title="Priority Alert Dispatch" className="mt-0 mb-0" />
          {criticalAlerts.length > 0 && (
            <button
              onClick={() => exportToCSV("priority_alerts", criticalAlerts)}
              className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5"
            >
              <Icon name="download" size={12} /> Export
            </button>
          )}
        </div>
        <Callout variant="info" className="mb-6">
          <b>Boolean Mask M&lt;sub&gt;i&lt;/sub&gt; = 1</b> if status &isin; {'{'}CRISIS, CRITICAL, LOW{'}'} · Layout Presentation Separation: backend computes mask, UI renders M=1 rows only.
        </Callout>

        {criticalAlerts.length === 0 ? (
          <Callout variant="good"><Icon name="check" size={14} className="inline mr-1" /> No priority alerts — all SKUs above LOW threshold.</Callout>
        ) : (
          <div className="mt-6 space-y-3">
            {criticalAlerts.map((alert, i) => (
              <div
                key={i}
                className={`
                  flex items-center gap-4 p-4 border-2
                  ${alert.status === "CRISIS" ? "bg-[#2E0A10] border-red" : ""}
                  ${alert.status === "CRITICAL" ? "bg-[#2A1404] border-[#FF6B00]" : ""}
                  ${alert.status === "LOW" ? "bg-[#2A2105] border-amber" : ""}
                `}
              >
                <div className="text-3xl font-extrabold min-w-[52px] text-center" style={{ color: STATUS_COLORS[alert.status] }}>
                  {alert.score}
                </div>
                <div className="flex-1">
                  <div className="font-bold text-text text-sm">{alert.sku}</div>
                  <div className="text-xs text-muted mt-1">{alert.explanation}</div>
                </div>
                <div className="text-center min-w-[52px]">
                  <div className="text-xl font-extrabold text-text">{alert.stock}</div>
                  <div className="text-[10px] text-muted">units</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
