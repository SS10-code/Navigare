"use client";

import { useState, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { isFeatureEnabled } from "@/lib/features";

const DEMO_MARGINS = [
  { name: "Latte", margin: 72.1, cost: 0.6, retail: 4.75 },
  { name: "Cold Brew", margin: 68.4, cost: 0.5, retail: 4.25 },
  { name: "Croissant", margin: 65.2, cost: 1.2, retail: 3.5 },
  { name: "Sourdough", margin: 58.3, cost: 2.5, retail: 7.5 },
  { name: "Baguette", margin: 45.0, cost: 1.0, retail: 3.5 },
  { name: "Red Velvet", margin: 38.5, cost: 3.2, retail: 7.0 },
];

const DEAD_STOCK = [
  { name: "Red Velvet Cake", stock: 45, cost: 3.2, capital: 144.0, sellThrough: 5.2 },
  { name: "Espresso Beans", stock: 28, cost: 8.5, capital: 238.0, sellThrough: 8.1 },
];

export default function ProfitPage() {
  const [price, setPrice] = useState(4.75);

  const getMarginColor = (m: number) => m >= 40 ? "#198754" : m >= 20 ? "#FFC107" : "#DC3545";

  if (!isFeatureEnabled("profit_optimizer")) {
    return (
      <div>
        <h1 className="text-[22px] font-extrabold text-text mb-1 tracking-tight">Profit Margin Optimizer</h1>
        <p className="text-[13.5px] text-muted mb-6">Gross margin per product · dead stock cost · price simulator</p>
        <Callout variant="warn">
          Profit optimization is disabled in guest mode. Create an account to unlock this feature.
        </Callout>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-[22px] font-extrabold text-text mb-1 tracking-tight">Profit Margin Optimizer</h1>
      <p className="text-[13.5px] text-muted mb-6">Gross margin per product · dead stock cost · price simulator</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Avg Margin</div>
          <div className="text-2xl font-extrabold text-text">58.2%</div>
          <div className="text-xs text-muted mt-1">across all products</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Best Margin</div>
          <div className="text-2xl font-extrabold text-teal">72.1%</div>
          <div className="text-xs text-muted mt-1">Latte</div>
        </Card>
        <Card padding="md">
          <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">Dead Stock</div>
          <div className="text-2xl font-extrabold text-red">$382</div>
          <div className="text-xs text-muted mt-1">capital tied up</div>
        </Card>
      </div>

      <Card className="mb-6">
        <SectionHeader title="Gross Margin by Product" />
        <div className="h-80 -mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={DEMO_MARGINS} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
              <XAxis type="number" stroke="#6B7280" fontSize={12} unit="%" />
              <YAxis dataKey="name" type="category" width={120} stroke="#6B7280" fontSize={12} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: "1px solid #E5E7EB", fontSize: 13 }}
                formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name === "margin" ? "Margin" : name]}
              />
              <Bar dataKey="margin" radius={[0, 8, 8, 0]} barSize={20}>
                {DEMO_MARGINS.map((entry) => (
                  <Cell key={entry.name} fill={getMarginColor(entry.margin)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex gap-6 mt-4 text-xs text-muted">
          <span className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-green-500 inline-block"></span> &gt;40%</span>
          <span className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-amber-400 inline-block"></span> 20–40%</span>
          <span className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-red-500 inline-block"></span> &lt;20%</span>
        </div>
      </Card>

      <Card className="mb-6">
        <SectionHeader title="What-If Price Simulator" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
          <div>
            <label className="block text-sm font-medium text-text mb-2">Product</label>
            <select className="w-full border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple">
              {DEMO_MARGINS.map((p) => (
                <option key={p.name} value={p.retail}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-2">New Price: ${price.toFixed(2)}</label>
            <input
              type="range"
              min={2}
              max={10}
              step={0.25}
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <Card padding="md" className="bg-bg border-border">
            <div className="text-[10.5px] font-semibold text-muted uppercase tracking-wider mb-1">New Margin</div>
            <div className="text-2xl font-extrabold text-green-500">
              {((price - 0.6) / price * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted mt-1">+{(price / 4.75 * 100 - 100).toFixed(0)}% price change</div>
          </Card>
        </div>
      </Card>

      <Card>
        <SectionHeader title="Dead Stock Cost Calculator" />
        <Callout variant="warn" className="mb-4">
          Products with sell-through below 10% are tying up capital that could be used for inventory that actually moves.
        </Callout>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Product</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Current Stock</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Cost Price</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Capital Tied Up</th>
                <th className="text-left py-3 px-4 text-[10.5px] font-semibold text-muted uppercase tracking-wider">Sell-Through</th>
              </tr>
            </thead>
            <tbody>
              {DEAD_STOCK.map((row, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-bg/50 transition">
                  <td className="py-3 px-4 font-medium text-text">{row.name}</td>
                  <td className="py-3 px-4 text-muted">{row.stock} units</td>
                  <td className="py-3 px-4 text-muted">${row.cost.toFixed(2)}</td>
                  <td className="py-3 px-4 font-bold text-red">${row.capital.toFixed(2)}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-50 text-red-600 border border-red-100">
                      {row.sellThrough}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 p-4 bg-red-50 border border-red-100 rounded-xl">
          <div className="text-sm font-semibold text-red-600">
            Total capital tied up in dead stock: $382.00
          </div>
        </div>
      </Card>
    </div>
  );
}
