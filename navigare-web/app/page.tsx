"use client";

import Link from "next/link";
import Icon from "@/components/Icon";
import { analytics } from "@/lib/analytics";
import { useRouter } from "next/navigation";
import { trackClient } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  const handleGuestMode = async () => {
    localStorage.setItem("navigare_guest_mode", "true");
    analytics.track("guest_session_start");
    await trackClient();
    router.push("/dashboard?guest=true");
  };

  return (
    <div className="min-h-screen bg-ink text-text flex items-center justify-center p-6 relative overflow-hidden">
      <div className="max-w-3xl text-center relative z-10">
        <div className="inline-flex items-center gap-2 border-2 border-teal text-teal px-4 py-1.5 mb-8 label-mono text-[11px] font-bold">
          <span className="w-2 h-2 bg-teal animate-pulse-soft inline-block" />
          THE OPS PERSON YOU CANNOT AFFORD TO HIRE
        </div>

        <h1 className="text-7xl font-black tracking-tighter uppercase leading-none mb-4">
          NAVI<span className="gradient-text">GARE</span>
        </h1>

        <p className="text-xl text-muted mb-10 font-mono max-w-xl mx-auto">
          retail analytics for local business owners — inventory, forecast, margins, churn.
          one dashboard. zero fluff.
        </p>

        <div className="flex gap-4 justify-center mb-16">
          <Link href="/auth/login" className="btn-primary inline-block">Log In</Link>
          <Link href="/auth/signup" className="btn-secondary inline-block">Sign Up</Link>
          <button
            onClick={handleGuestMode}
            className="btn-secondary inline-block"
          >
            Use Without Account
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 text-left" id="features">
          {[
            { icon: "box" as const, color: "#00FFC8", title: "Inventory Health", desc: "H(x) scoring, ROP alerts, wellness index. Never run out of stock again." },
            { icon: "trending" as const, color: "#FFB800", title: "Sales Forecast", desc: "Holt-Winters + EMA. Know what revenue to expect next week." },
            { icon: "users" as const, color: "#FF2E88", title: "Customer Segments", desc: "RFM scoring. Find champions, re-engage at-risk buyers." },
          ].map((f) => (
            <div key={f.title} className="bg-panel border-2 border-border p-6 card-hover" style={{ borderTop: `4px solid ${f.color}` }}>
              <div className="mb-3" style={{ color: f.color }}>
                <Icon name={f.icon} size={28} />
              </div>
              <h3 className="font-black text-text mb-1 uppercase text-sm tracking-wide">{f.title}</h3>
              <p className="text-sm text-muted font-mono text-[12px] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 flex items-center justify-center gap-8 text-muted font-mono text-[11px] border-t-2 border-border pt-6">
          <span>5 NEW MODULES</span>
          <span className="text-teal">ANOMALY RADAR</span>
          <span className="text-magenta">STOCKOUT CLOCK</span>
          <span className="text-amber">PRICE SIMULATOR</span>
        </div>
      </div>
    </div>
  );
}
