"use client";

import Sidebar from "@/components/Sidebar";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import Icon from "@/components/Icon";
import { isGuestMode } from "@/lib/auth";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/inventory": "Inventory Health",
  "/dashboard/combos": "What Sells Together",
  "/dashboard/customers": "Customer Segments",
  "/dashboard/forecast": "Sales Forecast",
  "/dashboard/seo": "SEO Auditor",
  "/dashboard/upload": "Upload Data",
  "/dashboard/profit": "Profit Optimizer",
  "/dashboard/digest": "Weekly Digest",
  "/dashboard/onboarding": "Onboarding",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [now, setNow] = useState("");
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    setNow(new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" }));
    setIsGuest(isGuestMode());
  }, []);

  return (
    <div className="min-h-screen bg-ink">
      <Sidebar />
      <main className="ml-64">
        {isGuest && (
          <div className="bg-amber/10 border-2 border-amber text-amber text-xs font-mono px-4 py-2 text-center">
            You are in guest mode. Some features are disabled. Create an account to unlock all features.
          </div>
        )}
        <div className="sticky top-0 z-40 bg-ink/90 backdrop-blur-md border-b-[3px] border-border px-8 py-3">
          <div className="flex items-center justify-between max-w-[1360px]">
            <div className="flex items-center gap-2 text-sm font-mono">
              <Icon name="logo" size={14} className="text-teal" />
              <span className="text-muted">DASHBOARD</span>
              <span className="text-border">/</span>
              <span className="font-bold text-text uppercase tracking-wide">{PAGE_TITLES[pathname] || "PAGE"}</span>
            </div>
            <div className="text-xs text-muted font-mono">{now}</div>
          </div>
        </div>
        <div className="max-w-[1360px] p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
