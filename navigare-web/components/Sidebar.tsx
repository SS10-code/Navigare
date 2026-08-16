"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Icon, { IconName } from "@/components/Icon";

const PAGES: { label: string; href: string; icon: IconName }[] = [
  { label: "Overview", href: "/dashboard", icon: "chart" },
  { label: "Inventory Health", href: "/dashboard/inventory", icon: "box" },
  { label: "What Sells Together", href: "/dashboard/combos", icon: "cart" },
  { label: "Customer Segments", href: "/dashboard/customers", icon: "users" },
  { label: "Sales Forecast", href: "/dashboard/forecast", icon: "trending" },
  { label: "SEO Auditor", href: "/dashboard/seo", icon: "search" },
  { label: "Upload Data", href: "/dashboard/upload", icon: "upload" },
  { label: "Profit Optimizer", href: "/dashboard/profit", icon: "cash" },
  { label: "Weekly Digest", href: "/dashboard/digest", icon: "mail" },
  { label: "Onboarding", href: "/dashboard/onboarding", icon: "rocket" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [wellness, setWellness] = useState<number | null>(null);
  const [alerts, setAlerts] = useState(0);

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

  const wellnessColor = wellness == null ? "text-muted" : wellness >= 70 ? "text-green" : wellness >= 40 ? "text-amber" : "text-red";
  const wellnessLabel = wellness == null ? "No data loaded" : wellness >= 70 ? "Store is Healthy" : wellness >= 40 ? "Needs attention" : "Critical - act now";

  return (
    <aside className="w-64 min-h-screen bg-panel border-r-[3px] border-border text-text flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6 pb-5 border-b-[3px] border-border">
        <Link href="/dashboard" className="flex items-center gap-3">
          <span className="text-blue"><Icon name="logo" size={30} /></span>
          <div>
            <div className="text-xl font-black tracking-tight uppercase">Navigare</div>
            <div className="text-[10px] text-muted tracking-[0.2em]">RETAIL ANALYTICS</div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 px-3 space-y-1 overflow-y-auto py-4">
        {PAGES.map((p) => {
          const active = pathname === p.href;
          return (
            <Link
              key={p.href}
              href={p.href}
              className={`
                flex items-center gap-3 px-3 py-2.5 border-2 transition-all duration-100
                ${active
                  ? "bg-blue text-white border-black shadow-[4px_4px_0_0_#000]"
                  : "border-transparent text-muted hover:bg-paper hover:text-text hover:border-border"
                }
              `}
            >
              <Icon name={p.icon} size={17} />
              <span className="text-[12.5px] font-bold tracking-wide uppercase">{p.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 space-y-2 border-t-[3px] border-border">
        <div className="bg-paper border-2 border-border p-3">
          <div className="text-[9px] text-muted uppercase tracking-[0.2em] mb-1">Store Wellness Index</div>
          <div className={`text-2xl font-black leading-none ${wellnessColor}`}>
            {wellness != null ? `${wellness}/100` : "--/100"}
          </div>
          <div className="text-[10px] text-muted mt-1">{wellnessLabel}</div>
        </div>

        <div className={`bg-paper border-2 p-3 ${alerts > 0 ? "border-red" : "border-border"}`}>
          <div className="flex items-center gap-2">
            {alerts > 0 && <Icon name="siren" size={14} className="text-red animate-pulse-soft" />}
            <div className={`text-[11px] font-bold uppercase ${alerts > 0 ? "text-red" : "text-muted"}`}>
              {alerts} Priority {alerts === 1 ? "Alert" : "Alerts"}
            </div>
          </div>
          <div className="text-[9.5px] text-muted mt-0.5">SKUs needing immediate action</div>
        </div>

        <Link href="/dashboard/onboarding" className="block text-center text-[10px] text-muted hover:text-text transition py-1">
          Settings / Onboarding
        </Link>
      </div>
    </aside>
  );
}
