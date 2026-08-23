"use client";

import { useState, useEffect } from "react";
import KPICard from "@/components/KPICard";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, Cell } from "recharts";
import { apiFetch } from "@/lib/api";
import { isFeatureEnabled } from "@/lib/features";

const COLORS = ["#7C5CFF", "#00FFC8", "#4DA3FF", "#FFB800", "#00E676", "#FF3B3B"];

type SegmentCounts = Record<string, number>;
type ScatterPoint = { x: number; y: number; segment: string; size: number };

const DEMO_SEGMENTS: SegmentCounts = { Champion: 8, Loyal: 12, Potential: 22, "At Risk": 18 };
const DEMO_SCATTER: ScatterPoint[] = [
  { x: 5, y: 450, segment: "Champion", size: 12 },
  { x: 12, y: 320, segment: "Loyal", size: 8 },
  { x: 25, y: 180, segment: "Potential", size: 5 },
  { x: 45, y: 90, segment: "At Risk", size: 3 },
  { x: 8, y: 520, segment: "Champion", size: 15 },
  { x: 18, y: 280, segment: "Loyal", size: 7 },
  { x: 35, y: 150, segment: "Potential", size: 4 },
  { x: 55, y: 60, segment: "At Risk", size: 2 },
];

export default function CustomersPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [segments, setSegments] = useState<SegmentCounts>({});
  const [scatter, setScatter] = useState<ScatterPoint[]>([]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const txnRows = [
        { Transaction_ID: "T1", Transaction_Date: "2026-08-01", Customer_ID: "C1", Line_Total_USD: 120 },
        { Transaction_ID: "T2", Transaction_Date: "2026-08-02", Customer_ID: "C2", Line_Total_USD: 85 },
        { Transaction_ID: "T3", Transaction_Date: "2026-08-03", Customer_ID: "C1", Line_Total_USD: 200 },
        { Transaction_ID: "T4", Transaction_Date: "2026-08-04", Customer_ID: "C3", Line_Total_USD: 45 },
        { Transaction_ID: "T5", Transaction_Date: "2026-08-05", Customer_ID: "C2", Line_Total_USD: 150 },
      ];
      const res = await apiFetch("/api/customers", {
        method: "POST",
        body: JSON.stringify({ rows: txnRows }),
      });

      const seg = res.segments ?? {};
      setSegments(seg);
      setScatter(
        Object.entries(seg).map(([segment, count], i) => ({
          x: [5, 12, 25, 45][i % 4],
          y: [450, 320, 180, 90][i % 4],
          segment,
          size: Math.max(5, Math.min(20, Number(count) * 2)),
        }))
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load customer data");
      setSegments(DEMO_SEGMENTS);
      setScatter(DEMO_SCATTER);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const segmentData = Object.entries(segments).length > 0
    ? Object.entries(segments).map(([name, value]) => ({ name, value }))
    : Object.entries(DEMO_SEGMENTS).map(([name, value]) => ({ name, value }));

  return (
    <div>
       <div className="flex items-center justify-between mb-6">
         <div>
           <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">Customer Segments</h1>
           <p className="text-[13px] text-muted font-mono">rfm scoring — recency, frequency, monetary</p>
         </div>
         {isFeatureEnabled("rfm") ? (
            <button onClick={loadData} disabled={loading} className="btn-primary flex items-center gap-2">
              {loading ? <><Icon name="loading" size={14} className="animate-spin" /> Loading...</> : <><Icon name="refresh" size={14} /> Refresh</>}
            </button>
         ) : (
           <Callout variant="warn" className="text-xs py-1 px-2">
             RFM analysis is disabled in guest mode.
           </Callout>
         )}
       </div>

      {error && (
        <Callout variant="danger" className="mb-6">
          {error} — showing demo data.
        </Callout>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <KPICard label="Customers" value={`${Object.values(segments).reduce((a, b) => a + b, 0) || 60}`} sub="All Stores" accent="teal" />
        <KPICard label="Champions" value={`${segments["Champion"] ?? 0}`} sub="top buyers" accent="green" />
        <KPICard label="Loyal" value={`${segments["Loyal"] ?? 0}`} sub="consistent" accent="purple" />
        <KPICard label="Potential" value={`${segments["Potential"] ?? 0}`} sub="growing" accent="blue" />
        <KPICard label="At Risk" value={`${segments["At Risk"] ?? 0}`} sub="need attention" accent="red" />
      </div>

      <Callout variant="info" className="mb-6">
        <b>Recency</b> — bought recently? 3=yes ·
        <b>Frequency</b> — how often? 3=frequent ·
        <b>Monetary</b> — how much? 3=high spender ·
        Score 3–9 to <b>Champion</b> (8–9) · <b>Loyal</b> (6–7) · <b>Potential</b> (4–5) · <b>At Risk</b> (3)
      </Callout>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <SectionHeader title="Customers by Segment" />
          <div className="h-64 -mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segmentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2A30" />
                <XAxis dataKey="name" stroke="#8A8A93" fontSize={12} />
                <YAxis stroke="#8A8A93" fontSize={12} />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 0, 0, 0]} barSize={40}>
                  {segmentData.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <SectionHeader title="Revenue by Segment" />
          <div className="h-64 -mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: "Champion", value: 18500 },
                { name: "Loyal", value: 14200 },
                { name: "Potential", value: 9800 },
                { name: "At Risk", value: 3200 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2A30" />
                <XAxis dataKey="name" stroke="#8A8A93" fontSize={12} />
                <YAxis stroke="#8A8A93" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]} />
                <Bar dataKey="value" radius={[0, 0, 0, 0]} barSize={40}>
                  {["Champion", "Loyal", "Potential", "At Risk"].map((name, index) => (
                    <Cell key={name} fill={COLORS[index]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card>
        <SectionHeader title="Recency vs Total Spend" />
        <div className="h-80 -mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A30" />
              <XAxis
                dataKey="x"
                type="number"
                name="Days Since Last Purchase"
                stroke="#8A8A93"
                fontSize={12}
              />
              <YAxis
                dataKey="y"
                type="number"
                name="Total Spend ($)"
                stroke="#8A8A93"
                fontSize={12}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === "Total Spend ($)") return [`$${value}`, "Spend"];
                  return [value, name];
                }}
              />
              <Scatter data={scatter.length > 0 ? scatter : DEMO_SCATTER} fill="#7C5CFF">
                {(scatter.length > 0 ? scatter : DEMO_SCATTER).map((entry, index) => (
                  <Cell key={index} fill={COLORS[["Champion", "Loyal", "Potential", "At Risk"].indexOf(entry.segment)]} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
