"use client";

import { useState, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { apiFetch } from "@/lib/api";

type DigestResponse = {
  status: string;
  email_id?: string;
};

export default function DigestPage() {
  const [email, setEmail] = useState("");
  const [day, setDay] = useState("1");
  const [time, setTime] = useState("08:00");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        recipient_email: email,
        store_name: "My Store",
        total_revenue: 48250,
        revenue_change_pct: 12.3,
        total_orders: 312,
        wellness_score: 72,
        wellness_interpretation: "Store is Healthy",
        priority_alerts: [
          { Product_Name: "Muffin", Health_Status: "CRISIS", Health_Explanation: "ZERO STOCK" },
          { Product_Name: "Red Velvet", Health_Status: "CRITICAL", Health_Explanation: "3 units left" },
        ],
        at_risk_customers: 8,
        top_combo: "Sourdough + Croissant",
        forecast_next_7d: 38100,
        seo_tip: "Add 'best bakery near me' to your Google Business description",
        week_start: "2026-08-01",
        week_end: "2026-08-07",
      };

      const res = await apiFetch("/api/digest", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send digest");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-[22px] font-extrabold text-text mb-1 tracking-tight">Weekly Email Digest</h1>
      <p className="text-[13.5px] text-muted mb-6">Get a plain-English summary every Monday — no login needed</p>

      {error && (
        <Callout variant="danger" className="mb-6">
          {error}
        </Callout>
      )}

      <Card className="max-w-lg">
        <SectionHeader title="Digest Preferences" />
        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-text mb-2">Digest Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple"
              placeholder="you@store.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-2">Day</label>
            <select
              value={day}
              onChange={(e) => setDay(e.target.value)}
              className="w-full border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple"
            >
              <option value="1">Monday</option>
              <option value="2">Tuesday</option>
              <option value="3">Wednesday</option>
              <option value="4">Thursday</option>
              <option value="5">Friday</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-2">Time</label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={loading || !email}
            className="bg-purple text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-opacity-90 transition w-full disabled:opacity-50"
          >
            {loading ? "Sending..." : "Send Test Digest"}
          </button>
          {saved && (
            <Callout variant="good">
              Test digest sent! Check your inbox. You&apos;ll receive your digest every week.
            </Callout>
          )}
        </div>
      </Card>

      <Card className="mt-8">
        <SectionHeader title="What You'll Receive" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          {[
            { icon: "cash" as const, title: "Revenue Summary", desc: "This week vs last week with % change" },
            { icon: "siren" as const, title: "Priority Alerts", desc: "CRISIS/CRITICAL SKUs with reorder suggestions" },
            { icon: "users" as const, title: "At-Risk Customers", desc: "Who hasn't purchased in 30+ days" },
            { icon: "cart" as const, title: "Top Combo", desc: "Best product pair this week" },
            { icon: "trending" as const, title: "7-Day Forecast", desc: "Holt-Winters revenue projection" },
            { icon: "search" as const, title: "SEO Tip", desc: "One keyword to add to your listing" },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-4 bg-bg rounded-xl border border-border">
              <div className="text-2xl text-blue"><Icon name={item.icon} size={24} /></div>
              <div>
                <div className="text-sm font-semibold text-text">{item.title}</div>
                <div className="text-xs text-muted mt-1">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
