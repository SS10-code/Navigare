"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Icon, { IconName } from "@/components/Icon";
import UserCounters from "@/components/UserCounters";
import { isGuestMode } from "@/lib/auth";

const PAGES: { label: string; href: string; icon: IconName }[] = [
  { label: "Overview", href: "/dashboard", icon: "chart" },
  { label: "Inventory", href: "/dashboard/inventory", icon: "box" },
  { label: "Combos", href: "/dashboard/combos", icon: "cart" },
  { label: "Customers", href: "/dashboard/customers", icon: "users" },
  { label: "Forecast", href: "/dashboard/forecast", icon: "trending" },
  { label: "SEO", href: "/dashboard/seo", icon: "search" },
  { label: "Upload", href: "/dashboard/upload", icon: "upload" },
  { label: "Profit", href: "/dashboard/profit", icon: "cash" },
  { label: "Digest", href: "/dashboard/digest", icon: "mail" },
  { label: "Setup", href: "/dashboard/onboarding", icon: "rocket" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [wellness, setWellness] = useState<number | null>(null);
  const [alerts, setAlerts] = useState(0);
  const [isGuest, setIsGuest] = useState(false);
  const [onboarding, setOnboarding] = useState(false);

  useEffect(() => {
    setIsGuest(isGuestMode());
    if (typeof window !== "undefined") {
      setOnboarding(!document.cookie.split("; ").some((c) => c.startsWith("navigare_onboarded=true")));
    }
  }, [pathname]);

  useEffect(() => {
    try {
      const inv = localStorage.getItem("navigare_inventory");
      if (inv) {
        const data = JSON.parse(inv);
        if (data.wellness != null) setWellness(data.wellness);
        const health = data.health ?? [];
        const count = health.filter(
          (r: Record<string, unknown>) =>
            ["CRISIS", "CRITICAL", "LOW"].includes(r.Health_Status as string)
        ).length;
        setAlerts(count);
      }
    } catch {
      /* ignore */
    }
  }, [pathname]);

  const wellnessColor = wellness == null ? "text-muted" : wellness >= 70 ? "text-accent" : wellness >= 40 ? "text-accent" : "text-accent";
  const wellnessLabel = wellness == null ? "No data" : wellness >= 70 ? "Healthy" : wellness >= 40 ? "Attention" : "Critical";

  return (
    <aside className="w-64 h-screen bg-panel border-r-2 border-border flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6 border-b-2 border-border">
        <Link href="/dashboard" className="flex items-center gap-3 no-underline">
          <span className="text-accent"><Icon name="logo" size={28} /></span>
          <div>
            <div className="text-xl font-bold uppercase tracking-tight text-ink" style={{ fontFamily: "Georgia, serif" }}>Navigare</div>
            <div className="text-[10px] text-muted tracking-[0.2em]">RETAIL ANALYTICS</div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        {!onboarding &&
          PAGES.map((p) => {
            const active = pathname === p.href;
            return (
              <Link
                key={p.href}
                href={p.href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 mb-1 border-l-2 transition-all duration-75 no-underline
                  ${active
                    ? "bg-paper border-l-accent text-ink font-bold"
                    : "border-l-transparent text-muted hover:bg-paper hover:text-ink hover:border-l-border"
                  }
                `}
              >
                <Icon name={p.icon} size={16} />
                <span className="text-[12px] font-semibold uppercase tracking-wide">{p.label}</span>
              </Link>
            );
          })
        }
        {onboarding && (
          <div className="px-3 py-4">
            <div className="text-caption text-muted mb-3">Setup in progress</div>
            <p className="text-sm text-muted leading-relaxed">
              Upload your data to unlock the full dashboard, or skip to continue with sample data.
            </p>
          </div>
        )}
      </nav>

      <div className="p-4 border-t-2 border-border">
        <div className="bg-paper border-2 border-border p-4 mb-3">
          <div className="text-caption text-muted mb-2">Store Wellness</div>
          <div className={`text-2xl font-bold leading-none ${wellnessColor}`}>
            {wellness != null ? `${wellness}/100` : "--/100"}
          </div>
          <div className="text-[10px] text-muted mt-1">{wellnessLabel}</div>
        </div>

        <div className={`bg-paper border-2 p-3 mb-3 ${alerts > 0 ? "border-accent" : "border-border"}`}>
          <div className="flex items-center gap-2">
            {alerts > 0 && <Icon name="siren" size={14} className="text-accent" />}
            <div className={`text-[11px] font-bold uppercase ${alerts > 0 ? "text-accent" : "text-muted"}`}>
              {alerts} Priority {alerts === 1 ? "Alert" : "Alerts"}
            </div>
          </div>
        </div>

        <UserCounters />

        {!onboarding && (
          <Link href="/dashboard/onboarding" className="block text-center text-[10px] text-muted hover:text-ink transition py-2 no-underline">
            Settings / Onboarding
          </Link>
        )}
        <Link href="/legal" className="block text-center text-[10px] text-muted hover:text-ink transition py-2 no-underline">
          Legal / Terms
        </Link>
      </div>
    </aside>
  );
}
