"use client";

import Link from "next/link";
import Icon from "@/components/Icon";
import { analytics } from "@/lib/analytics";
import { useRouter } from "next/navigation";
import { trackClient } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  const handleGuestMode = async () => {
    document.cookie = "navigare_guest_mode=true; path=/; max-age=" + 7 * 24 * 60 * 60;
    document.cookie = "navigare_onboarded=false; path=/; max-age=" + 7 * 24 * 60 * 60;
    analytics.track("guest_session_start");
    await trackClient();
    setTimeout(() => {
      window.location.href = "/dashboard/upload?onboarding=true&guest=true";
    }, 100);
  };

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="max-w-[1200px] mx-auto px-8 py-16">
        <div className="grid grid-cols-12 gap-8">
          <div className="col-span-7">
            <div className="text-caption text-muted mb-6">RETAIL ANALYTICS</div>
            <h1 className="text-display text-[72px] mb-6 leading-none">
              NAVI<span className="text-accent">GARE</span>
            </h1>
            <p className="text-body text-lg text-muted max-w-lg mb-10 leading-relaxed">
              Retail analytics for local business owners. Inventory, forecast, margins, churn — one dashboard, zero fluff.
            </p>
            <div className="flex gap-3">
              <Link href="/auth/signup" className="btn-primary">Sign Up</Link>
              <Link href="/auth/login" className="btn-secondary">Log In</Link>
              <button onClick={handleGuestMode} className="btn-secondary">
                Use Without Account
              </button>
            </div>
          </div>
          <div className="col-span-5 flex flex-col gap-6 pt-12">
            {[
              { icon: "box" as const, title: "Inventory Health", desc: "H(x) scoring, ROP alerts, wellness index." },
              { icon: "trending" as const, title: "Sales Forecast", desc: "Holt-Winters + EMA. Know what revenue to expect next week." },
              { icon: "users" as const, title: "Customer Segments", desc: "RFM scoring. Find champions, re-engage at-risk buyers." },
            ].map((f, i) => (
              <div key={f.title} className="border-2 border-border p-6 bg-panel hover:border-accent transition-colors" style={{ borderTop: `4px solid ${i === 0 ? "var(--accent)" : "var(--border)"}` }}>
                <div className="flex items-start gap-4">
                  <div className="text-accent"><Icon name={f.icon} size={24} /></div>
                  <div>
                    <h3 className="text-headline text-base font-bold uppercase tracking-wide mb-1">{f.title}</h3>
                    <p className="text-body text-sm text-muted leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="border-t border-border mt-16">
        <div className="max-w-[1200px] mx-auto px-8 py-4 flex justify-between text-xs text-muted">
          <span>© 2026 Navigare</span>
          <Link href="/feedback" className="text-accent hover:underline">Send Feedback</Link>
        </div>
      </div>
    </div>
  );
}
