"use client";

import { useState, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";

const STORE_TYPES = ["Retail", "Food/Bakery", "Service", "E-Commerce"];
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [storeType, setStoreType] = useState("");
  const [storeName, setStoreName] = useState("");
  const [threshold, setThreshold] = useState(10);
  const [email, setEmail] = useState("");
  const [day, setDay] = useState("Monday");
  const [time, setTime] = useState("08:00");

  const canNext = step === 1 ? !!(storeType && storeName) : true;

  const savePreferences = async () => {
    try {
      await fetch("/api/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ storeType, storeName, threshold, email, day, time }),
      });
      localStorage.setItem("navigare_onboarded", "true");
      alert("Setup complete! Welcome to Navigare.");
    } catch {
      localStorage.setItem("navigare_onboarded", "true");
      alert("Setup complete! Welcome to Navigare.");
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-[22px] font-extrabold text-text mb-1 tracking-tight">First-Time Setup</h1>
      <p className="text-[13.5px] text-muted mb-8">Get Navigare tailored to your store in 4 steps.</p>

      <div className="flex items-center gap-2 mb-10">
        {[1, 2, 3, 4].map((s) => (
          <div key={s} className="flex items-center gap-2 flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition ${
                s <= step ? "bg-purple text-white" : "bg-border text-muted"
              }`}
            >
              {s}
            </div>
            {s < 4 && (
              <div
                className="flex-1 h-0.5 transition"
                style={{ backgroundColor: s < step ? "#423A8E" : "#E5E7EB" }}
              ></div>
            )}
          </div>
        ))}
      </div>

      <Card>
        {step === 1 && (
          <div>
            <SectionHeader title="What kind of store are you?" />
            <div className="grid grid-cols-2 gap-3 mb-6">
              {STORE_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setStoreType(t)}
                  className={`p-4 rounded-xl border-2 text-sm font-medium transition ${
                    storeType === t
                      ? "border-purple bg-purple/5 text-purple"
                      : "border-border text-muted hover:border-purple/50"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              placeholder="Store name"
              className="w-full border border-border rounded-xl px-4 py-2.5 text-sm mb-6 focus:outline-none focus:ring-2 focus:ring-purple"
            />
            <button
              onClick={() => setStep(2)}
              disabled={!canNext}
              className="bg-purple text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-opacity-90 transition disabled:opacity-50 w-full"
            >
              Next →
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <SectionHeader title="Upload your sales data" />
            <Callout variant="info" className="mb-6">
              Download our sample CSV, fill it with your data, then upload it here.
            </Callout>
            <div className="border-2 border-dashed border-border rounded-xl p-8 text-center mb-6">
              <div className="text-4xl mb-3 text-blue"><Icon name="file" size={40} /></div>
              <p className="text-sm text-muted mb-4">Drag & drop your CSV here</p>
              <input type="file" accept=".csv" className="block w-full text-sm text-muted mx-auto" />
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="flex-1 border border-border px-6 py-2.5 rounded-xl font-semibold text-muted hover:text-text transition">
                ← Back
              </button>
              <button onClick={() => setStep(3)} className="flex-1 bg-purple text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-opacity-90 transition">
                Next →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <SectionHeader title="Set restock thresholds" />
            <Callout variant="info" className="mb-6">
              Alert me when stock falls below <b>{threshold}</b> units
            </Callout>
            <input
              type="range"
              min="5"
              max="50"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full mb-8"
            />
            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="flex-1 border border-border px-6 py-2.5 rounded-xl font-semibold text-muted hover:text-text transition">
                ← Back
              </button>
              <button onClick={() => setStep(4)} className="flex-1 bg-purple text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-opacity-90 transition">
                Next →
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <SectionHeader title="Set up weekly digest email" />
            <div className="space-y-5 mb-8">
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
                  {DAYS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
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
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(3)} className="flex-1 border border-border px-6 py-2.5 rounded-xl font-semibold text-muted hover:text-text transition">
                ← Back
              </button>
              <button onClick={savePreferences} className="flex-1 bg-purple text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-opacity-90 transition">
                Finish Setup
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
