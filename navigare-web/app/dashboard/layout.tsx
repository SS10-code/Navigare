"use client";

import Sidebar from "@/components/Sidebar";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import Icon from "@/components/Icon";
import { isGuestMode, isOnboarded } from "@/lib/auth";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/inventory": "Inventory",
  "/dashboard/combos": "Combos",
  "/dashboard/customers": "Customers",
  "/dashboard/forecast": "Forecast",
  "/dashboard/seo": "SEO",
  "/dashboard/upload": "Upload",
  "/dashboard/profit": "Profit",
  "/dashboard/digest": "Digest",
  "/dashboard/onboarding": "Setup",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [now, setNow] = useState("");
  const [isGuest, setIsGuest] = useState(false);
  const [showOnboardingBanner, setShowOnboardingBanner] = useState(false);

  useEffect(() => {
    setNow(new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" }));
    setIsGuest(isGuestMode());
    setShowOnboardingBanner(!isOnboarded());
  }, [pathname]);

  return (
    <div className="min-h-screen bg-paper">
      <Sidebar />
      <main className="ml-64">
        {isGuest && (
          <div className="bg-accent/10 border-l-4 border-accent text-accent text-xs font-mono px-6 py-3">
            Guest mode — create an account to unlock all features.
          </div>
        )}
        {showOnboardingBanner && (
          <div className="bg-paper border-l-4 border-accent text-ink text-xs font-mono px-6 py-3">
            Complete setup: upload your data or skip to continue with sample data.
          </div>
        )}
        <div className="sticky top-0 z-40 bg-paper border-b-2 border-border px-8 py-4">
          <div className="flex items-center justify-between max-w-[1360px]">
            <div className="flex items-center gap-3">
              <Icon name="logo" size={14} className="text-accent" />
              <span className="text-caption text-muted">DASHBOARD</span>
              <span className="text-border">/</span>
              <span className="font-bold text-ink uppercase tracking-wide text-sm">{PAGE_TITLES[pathname] || "PAGE"}</span>
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
