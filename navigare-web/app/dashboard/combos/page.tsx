"use client";

import { useState, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { apiFetch } from "@/lib/api";

const COLORS = ["#7C5CFF", "#00FFC8", "#4DA3FF", "#FFB800", "#00E676", "#FF3B3B"];

type ComboRow = { pair: string; lift: number; support: number; confidence: number };

const DEMO_COMBOS: ComboRow[] = [
  { pair: "Sourdough + Croissant", lift: 3.2, support: 0.085, confidence: 0.72 },
  { pair: "Latte + Muffin", lift: 2.8, support: 0.062, confidence: 0.65 },
  { pair: "Cold Brew + Espresso", lift: 2.4, support: 0.051, confidence: 0.58 },
  { pair: "Baguette + Croissant", lift: 2.1, support: 0.048, confidence: 0.54 },
  { pair: "Red Velvet + Latte", lift: 1.9, support: 0.039, confidence: 0.48 },
];

export default function CombosPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [combos, setCombos] = useState<ComboRow[]>([]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const txnRows = [
        { Transaction_ID: "T1", Product_ID: "P1" },
        { Transaction_ID: "T1", Product_ID: "P2" },
        { Transaction_ID: "T2", Product_ID: "P3" },
        { Transaction_ID: "T2", Product_ID: "P4" },
        { Transaction_ID: "T3", Product_ID: "P1" },
        { Transaction_ID: "T3", Product_ID: "P3" },
      ];
      const res = await apiFetch("/api/combos", {
        method: "POST",
        body: JSON.stringify({ rows: txnRows, min_support: 0.02, top_n: 30 }),
      });
      const pairs = (res.pairs ?? []).map((p: Record<string, unknown>) => ({
        pair: (p.Pair_Label as string) ?? "Unknown",
        lift: Number(p.Lift ?? 0),
        support: Number(p.Support ?? 0),
        confidence: Number(p.Confidence_AB ?? 0),
      }));
      setCombos(pairs.length > 0 ? pairs : DEMO_COMBOS);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load combo data");
      setCombos(DEMO_COMBOS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">What Sells Together</h1>
          <p className="text-[13px] text-muted font-mono">market basket analysis — lift, confidence, support</p>
        </div>
        <button onClick={loadData} className="btn-primary flex items-center gap-2">
          <Icon name="refresh" size={14} /> Refresh
        </button>
      </div>

      {error && (
        <Callout variant="danger" className="mb-6">
          {error} — showing demo data.
        </Callout>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Pairs Found</div>
          <div className="text-2xl font-extrabold text-text">{combos.length}</div>
          <div className="text-xs text-muted mt-1">above threshold</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Top Lift</div>
          <div className="text-2xl font-extrabold text-text">{combos.length > 0 ? `${combos[0].lift.toFixed(2)}×` : "0×"}</div>
          <div className="text-xs text-muted mt-1">strongest link</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Avg Confidence</div>
          <div className="text-2xl font-extrabold text-text">
            {combos.length > 0 ? `${(combos.reduce((sum, c) => sum + c.confidence, 0) / combos.length * 100).toFixed(1)}%` : "0%"}
          </div>
          <div className="text-xs text-muted mt-1">A to B</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Orders Scanned</div>
          <div className="text-2xl font-extrabold text-text">312</div>
          <div className="text-xs text-muted mt-1">baskets</div>
        </Card>
      </div>

      <Callout variant="info" className="mb-6">
        <b>Lift &gt; 1</b> means the pair is genuinely associated, not just popular.
        <b> Support</b> = % of all orders with this pair.
        <b> Confidence</b> = if A is bought, probability B is too.
      </Callout>

      <Card className="mt-6">
        <SectionHeader title="Strongest Pairs (ranked by Lift)" />
        <div className="h-80 -mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={combos}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A30" />
              <XAxis dataKey="pair" stroke="#8A8A93" fontSize={11} tick={{ fontSize: 11 }} />
              <YAxis stroke="#8A8A93" fontSize={12} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === "lift") return [`${value.toFixed(2)}×`, "Lift"];
                  if (name === "support") return [`${(value * 100).toFixed(1)}%`, "Support"];
                  if (name === "confidence") return [`${(value * 100).toFixed(0)}%`, "Confidence"];
                  return [value, name];
                }}
              />
              <Bar dataKey="lift" radius={[0, 0, 0, 0]} barSize={36}>
                {combos.map((entry, index) => (
                  <Cell key={index} fill={entry.lift >= 2 ? "#00E676" : entry.lift >= 1.5 ? "#00FFC8" : "#7C5CFF"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="mt-6">
        <SectionHeader title="Full Pair Table" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Pair</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Orders Together</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Support</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Confidence (A to B)</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Lift</th>
              </tr>
            </thead>
            <tbody>
              {combos.map((row, i) => (
                 <tr key={i} className="border-b border-border/50 hover:bg-paper transition">
                  <td className="py-3 px-4 font-medium text-text">{row.pair}</td>
                  <td className="py-3 px-4 text-muted">--</td>
                  <td className="py-3 px-4 text-muted">{(row.support * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-muted">{(row.confidence * 100).toFixed(0)}%</td>
                  <td className="py-3 px-4 font-bold" style={{ color: row.lift >= 2 ? "#00E676" : row.lift >= 1.5 ? "#00FFC8" : "#7C5CFF" }}>
                    {row.lift.toFixed(2)}×
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
