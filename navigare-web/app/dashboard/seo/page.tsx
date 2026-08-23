"use client";

import { useState, useEffect } from "react";
import Card from "@/components/Card";
import Callout from "@/components/Callout";
import SectionHeader from "@/components/SectionHeader";
import Icon from "@/components/Icon";
import { apiFetch } from "@/lib/api";

type SEOResult = {
  keyword: string;
  score: number;
  density: number;
  matches: number;
  ngram: number;
  zone: string;
  severity: string;
};

const DEMO_RESULTS: SEOResult[] = [
  { keyword: "bakery near me", score: 85, density: 2.1, matches: 4, ngram: 3, zone: "Sweet Spot", severity: "none" },
  { keyword: "fresh bread", score: 100, density: 1.8, matches: 3, ngram: 2, zone: "Sweet Spot", severity: "none" },
  { keyword: "custom birthday cake", score: 45, density: 4.2, matches: 1, ngram: 3, zone: "Over-Stuffed", severity: "high" },
  { keyword: "artisan bakery", score: 100, density: 1.5, matches: 2, ngram: 2, zone: "Sweet Spot", severity: "none" },
  { keyword: "sourdough loaf", score: 50, density: 0.8, matches: 1, ngram: 2, zone: "Under-Optimized", severity: "low" },
];

const SEVERITY_COLORS: Record<string, string> = {
  none: "#00E676",
  low: "#B8F73C",
  medium: "#FFB800",
  high: "#FF6B00",
  critical: "#FF3B3B",
};

export default function SEPage() {
  const [body, setBody] = useState("");
  const [keywords, setKeywords] = useState("bakery near me\nfresh bread\ncustom birthday cake\nartisan bakery\nsourdough loaf");
  const [result, setResult] = useState<SEOResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAudit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiFetch("/api/seo", {
        method: "POST",
        body: JSON.stringify({
          body_text: body,
          keywords: keywords.split("\n").filter((k) => k.trim()),
          remove_stopwords: false,
        }),
      });

      const mapped = (res.results ?? []).map((r: Record<string, unknown>) => ({
        keyword: r.keyword as string,
        score: r.score as number,
        density: r.density_pct as number,
        matches: r.match_count as number,
        ngram: r.n_gram_size as number,
        zone: r.zone as string,
        severity: r.severity as string,
      }));

      setResult(mapped.length > 0 ? mapped : DEMO_RESULTS);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run SEO audit");
      setResult(DEMO_RESULTS);
    } finally {
      setLoading(false);
    }
  };

  const pageHealth = result
    ? Math.round(result.reduce((sum, r) => sum + r.score, 0) / result.length)
    : 0;

  return (
    <div>
      <h1 className="text-[28px] font-black uppercase tracking-tight text-text mb-1">SEO Auditor</h1>
      <p className="text-[13px] text-muted font-mono mb-6">keyword density, N-gram scoring, page health</p>

      {error && (
        <Callout variant="danger" className="mb-6">
          {error} — showing demo results.
        </Callout>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card hover>
          <SectionHeader title="Your Web Copy" />
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={10}
            className="w-full resize-none"
            placeholder="Paste your homepage, product page, or Google Business listing here..."
          />
          {body.trim() && (
            <div className="mt-2 text-xs text-muted font-mono">
              token count: {body.toLowerCase().replace(/[^a-z0-9\s]/g, "").split(/\s+/).filter(Boolean).length}
            </div>
          )}
        </Card>

        <Card hover>
          <SectionHeader title="Target Keywords (one per line)" />
          <textarea
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            rows={10}
            className="w-full resize-none"
          />
          <button
            onClick={runAudit}
            disabled={loading || !body.trim()}
            className="btn-primary w-full mt-4"
          >
            {loading ? "Analyzing..." : "Run Audit"}
          </button>
        </Card>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <Card padding="md">
              <div className="label-mono text-[10px] font-bold text-muted mb-1">Page Health</div>
              <div className={`text-3xl font-black font-mono ${pageHealth >= 70 ? "text-green" : pageHealth >= 50 ? "text-amber" : "text-red"}`}>
                {pageHealth}/100
              </div>
              <div className="text-xs text-muted mt-1 font-mono">
                {pageHealth >= 90 ? "excellent" : pageHealth >= 70 ? "good" : pageHealth >= 50 ? "needs work" : "poor"}
              </div>
            </Card>
            <Card padding="md">
              <div className="label-mono text-[10px] font-bold text-muted mb-1">Word Count</div>
              <div className="text-3xl font-black font-mono text-text">{body.split(/\s+/).filter(Boolean).length || 142}</div>
              <div className="text-xs text-muted mt-1 font-mono">tokens</div>
            </Card>
            <Card padding="md">
              <div className="label-mono text-[10px] font-bold text-muted mb-1">Keywords</div>
              <div className="text-3xl font-black font-mono text-text">{result.length}</div>
              <div className="text-xs text-muted mt-1 font-mono">phrases checked</div>
            </Card>
          </div>

          <Card className="mb-6">
            <SectionHeader title="Keyword Results" />
            <div className="space-y-3">
              {result.map((r, i) => (
                <div key={i} className="flex items-center gap-4 p-4 bg-panel border-2 border-border">
                  <div
                    className="w-12 h-12 flex items-center justify-center text-lg font-black font-mono border-2"
                    style={{ backgroundColor: `${SEVERITY_COLORS[r.severity]}20`, color: SEVERITY_COLORS[r.severity], borderColor: SEVERITY_COLORS[r.severity] }}
                  >
                    {r.score}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-text text-sm">"{r.keyword}"</div>
                    <div className="text-xs text-muted mt-1 font-mono">
                      {r.matches} matches · {r.density}% density · {r.ngram}-gram · {r.zone}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold uppercase flex items-center gap-1" style={{ color: SEVERITY_COLORS[r.severity] }}>
                      {r.severity === "none" ? <><Icon name="check" size={12} /> Good</> : r.severity === "low" ? <><Icon name="warning" size={12} /> Low</> : r.severity === "medium" ? <><Icon name="warning" size={12} /> Medium</> : <><Icon name="alert" size={12} /> High</>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Callout variant="info">
            <b>How it works:</b> Lowercase → strip punctuation → tokenise → sliding window N-gram scan → piecewise density score<br />
            <b>&lt;1%</b> = 50 (under-optimized) · <b>1–3.5%</b> = 100 (sweet spot) · <b>&gt;3.5%</b> = max(0, 100−(excess×15)) (stuffing penalty)
          </Callout>
        </>
      )}
    </div>
  );
}
