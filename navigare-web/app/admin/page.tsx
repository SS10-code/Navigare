"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";

const ADMIN_PASSWORD = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "navigare_admin_2026";

type Counters = {
  business_clients: number;
  clients: number;
  onboarded: number;
  total_clients: number;
};

export default function AdminPage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [counters, setCounters] = useState<Counters>({ business_clients: 0, clients: 0, onboarded: 0, total_clients: 0 });
  const [apiError, setApiError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchCounters = async () => {
    setApiError(null);
    try {
      const data = await apiFetch("/counters");
      setCounters(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (e) {
      setApiError(e instanceof Error ? e.message : "Failed to load counters");
    }
  };

  useEffect(() => {
    if (authenticated) {
      fetchCounters();
      const interval = setInterval(fetchCounters, 2000);
      return () => clearInterval(interval);
    }
  }, [authenticated]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === ADMIN_PASSWORD) {
      setAuthenticated(true);
      setError("");
    } else {
      setError("Invalid password");
    }
  };

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-paper text-ink flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <h1 className="text-display text-2xl font-bold uppercase tracking-tight">Admin</h1>
            <p className="text-caption text-muted text-[10px] mt-1">Enter password to view stats</p>
          </div>
          <div className="border-2 border-border bg-panel p-8">
            {error && (
              <div className="bg-accent/10 border-2 border-accent text-accent px-4 py-3 text-sm mb-6 font-mono">{error}</div>
            )}
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="text-caption text-muted text-[10px] block mb-2">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full"
                  required
                />
              </div>
              <button type="submit" className="btn-primary w-full">Access Admin</button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper text-ink flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-10">
          <h1 className="text-display text-3xl font-bold uppercase tracking-tight">Client Statistics</h1>
          <p className="text-caption text-muted text-[10px] mt-2">Admin view — confidential</p>
          {lastUpdated && (
            <p className="text-[10px] text-muted mt-1 font-mono">Last updated: {lastUpdated}</p>
          )}
        </div>

        {apiError && (
          <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 text-sm mb-6 font-mono">
            API Error: {apiError}
          </div>
        )}

        <div className="border-2 border-border bg-panel p-8 mb-8">
          <div className="grid grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-caption text-muted mb-2">Business Clients</div>
              <div className="text-4xl font-bold text-accent" style={{ fontFamily: "Georgia, serif" }}>{counters.business_clients}</div>
              <div className="text-xs text-muted mt-1">Email signups</div>
            </div>
            <div className="text-center">
              <div className="text-caption text-muted mb-2">Clients</div>
              <div className="text-4xl font-bold text-ink" style={{ fontFamily: "Georgia, serif" }}>{counters.clients}</div>
              <div className="text-xs text-muted mt-1">Guest sessions</div>
            </div>
            <div className="text-center">
              <div className="text-caption text-muted mb-2">Onboarded</div>
              <div className="text-4xl font-bold text-green-600" style={{ fontFamily: "Georgia, serif" }}>{counters.onboarded}</div>
              <div className="text-xs text-muted mt-1">Completed setup</div>
            </div>
            <div className="text-center">
              <div className="text-caption text-muted mb-2">Total Clients</div>
              <div className="text-4xl font-bold text-accent" style={{ fontFamily: "Georgia, serif" }}>{counters.total_clients}</div>
              <div className="text-xs text-muted mt-1">Combined total</div>
            </div>
          </div>
        </div>

        <div className="text-center">
          <button onClick={() => setAuthenticated(false)} className="btn-secondary">Log Out</button>
        </div>
      </div>
    </div>
  );
}
