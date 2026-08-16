"use client";

import { useState, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, Cell } from "recharts";
import { apiFetch } from "@/lib/api";

type ForecastData = {
  dates: string[];
  actuals: number[];
  sma: number[];
  ema: number[];
  hw_fitted?: number[];
  hw_forecast?: { date: string; value: number }[];
  hw_mae?: number;
  sma_mae?: number;
  ema_mae?: number;
};

const DEMO_FORECAST: ForecastData = {
  dates: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  actuals: [4200, 3800, 5100, 4600, 6200, 7800, 5500],
  sma: [4200, 4000, 4366, 4566, 5166, 5866, 5500],
  ema: [4200, 4066, 4373, 4566, 5106, 5786, 5500],
  hw_fitted: [4200, 3900, 4800, 4600, 5900, 7200, 5800],
  hw_forecast: [
    { date: "Mon", value: 5200 },
    { date: "Tue", value: 5400 },
    { date: "Wed", value: 5100 },
    { date: "Thu", value: 5600 },
    { date: "Fri", value: 6100 },
    { date: "Sat", value: 6800 },
    { date: "Sun", value: 5900 },
  ],
  hw_mae: 156.2,
  sma_mae: 245.3,
  ema_mae: 198.7,
};

export default function ForecastPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ForecastData | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const txnRows = [
        { Transaction_ID: "T1", Transaction_Date: "2026-07-01", Line_Total_USD: 120 },
        { Transaction_ID: "T2", Transaction_Date: "2026-07-02", Line_Total_USD: 85 },
        { Transaction_ID: "T3", Transaction_Date: "2026-07-03", Line_Total_USD: 200 },
        { Transaction_ID: "T4", Transaction_Date: "2026-07-04", Line_Total_USD: 45 },
        { Transaction_ID: "T5", Transaction_Date: "2026-07-05", Line_Total_USD: 150 },
        { Transaction_ID: "T6", Transaction_Date: "2026-07-06", Line_Total_USD: 180 },
        { Transaction_ID: "T7", Transaction_Date: "2026-07-07", Line_Total_USD: 220 },
      ];
      const res = await apiFetch("/api/forecast", {
        method: "POST",
        body: JSON.stringify({ rows: txnRows, forecast_days: 7, ema_span: 7, seasonal_period: 7 }),
      });
      setData(res as ForecastData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load forecast data");
      setData(DEMO_FORECAST);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted text-sm">Loading forecast data...</div>
      </div>
    );
  }

  const combined = data.dates.map((date, i) => ({
    date,
    actual: data.actuals[i] ?? 0,
    sma: data.sma[i] ?? 0,
    ema: data.ema[i] ?? 0,
    hw_fitted: data.hw_fitted?.[i] ?? null,
  }));

  const forecastPoints = data.hw_forecast ?? [];

  const accuracy = [
    { model: "SMA-7", mae: data.sma_mae ?? 245.3 },
    { model: "EMA-7", mae: data.ema_mae ?? 198.7 },
    { model: "Holt-Winters", mae: data.hw_mae ?? 156.2 },
  ];
  const bestModel = accuracy.reduce((a, b) => (a.mae < b.mae ? a : b)).model;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">Sales Forecast</h1>
          <p className="text-[13px] text-muted font-mono">sma, ema, and holt-winters projections</p>
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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">SMA Window</div>
          <div className="text-2xl font-extrabold text-text">7 days</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">EMA Span</div>
          <div className="text-2xl font-extrabold text-text">7 days</div>
          <div className="text-xs text-muted mt-1">α = 0.250</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Seasonal Period</div>
          <div className="text-2xl font-extrabold text-text">7 days</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Forecast Days</div>
          <div className="text-2xl font-extrabold text-text">7 days</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Best Model</div>
          <div className="text-2xl font-extrabold text-green">{bestModel}</div>
          <div className="text-xs text-muted mt-1 flex items-center gap-1">
            <Icon name="bolt" size={14} /> Most accurate
          </div>
        </Card>
      </div>

      <Callout variant="info" className="mb-6">
        <b>Simple Moving Average</b> — Last 7 days averaged equally. Smooth, but lags behind change.<br />
        <b>Weighted Avg (EMA)</b> — Recent days count more. α=0.250 weights today vs yesterday.<br />
        <b>Holt-Winters</b> — Tracks level + trend + 7-day seasonality simultaneously.
      </Callout>

      <Card className="mb-6">
        <SectionHeader title="Revenue + Forecast" />
        <div className="h-80 -mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={combined}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2A30" />
              <XAxis dataKey="date" stroke="#8A8A93" fontSize={12} />
              <YAxis stroke="#8A8A93" fontSize={12} tickFormatter={(v) => `$${v}`} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="actual" stroke="#7C5CFF" strokeWidth={2} name="Actual" dot={{ r: 4, fill: "#7C5CFF" }} />
              <Line type="monotone" dataKey="sma" stroke="#FFB800" strokeWidth={2} strokeDasharray="5 5" name="SMA-7" dot={{ r: 4, fill: "#FFB800" }} />
              <Line type="monotone" dataKey="ema" stroke="#00FFC8" strokeWidth={2} name="EMA-7" dot={{ r: 4, fill: "#00FFC8" }} />
              {data.hw_fitted && data.hw_fitted.length > 0 && (
                <Line type="monotone" dataKey="hw_fitted" stroke="#00E676" strokeWidth={2} name="HW Fitted" dot={{ r: 4, fill: "#00E676" }} connectNulls />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {forecastPoints.length > 0 && (
        <Card className="mb-6">
          <SectionHeader title="7-Day Forecast" />
          <div className="h-64 -mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastPoints}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2A30" />
                <XAxis dataKey="date" stroke="#8A8A93" fontSize={12} />
                <YAxis stroke="#8A8A93" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="value" stroke="#00FFC8" strokeWidth={2.5} strokeDasharray="5 5" name="HW Forecast +7d" dot={{ r: 5, fill: "#00FFC8" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <Card>
        <SectionHeader title="Model Accuracy (avg daily error)" />
        <div className="h-64 -mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={accuracy}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="model" stroke="#6B7280" fontSize={12} />
              <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(v) => `$${v}`} />
              <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}/day`, "MAE"]} contentStyle={{ borderRadius: 12, border: "1px solid #E5E7EB", fontSize: 13 }} />
              <Bar dataKey="mae" radius={[8, 8, 0, 0]} barSize={48}>
                {accuracy.map((entry) => (
                  <Cell key={entry.model} fill={entry.model === bestModel ? "#198754" : "#423A8E"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
