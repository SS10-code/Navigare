type Accent = "default" | "accent";

const ACCENT_COLORS: Record<Accent, string> = {
  default: "#6B6B6B",
  accent: "#D4380D",
};

interface Props {
  label: string;
  value: string;
  sub: string;
  accent?: Accent;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}

export default function KPICard({ label, value, sub, accent = "default", icon, trend }: Props) {
  const color = ACCENT_COLORS[accent];
  return (
    <div
      className="border-2 border-border bg-panel p-5 relative overflow-hidden animate-fade-in"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="text-caption text-muted text-[10px]">{label}</div>
        {icon && <div className="text-muted">{icon}</div>}
      </div>
      <div className="text-3xl font-bold text-ink tracking-tight mb-1" style={{ fontFamily: "Georgia, serif" }}>{value}</div>
      <div className="flex items-center gap-1">
        {trend === "up" && <span className="text-accent text-xs font-bold">&#8593;</span>}
        {trend === "down" && <span className="text-accent text-xs font-bold">&#8595;</span>}
        <div className="text-[11px] text-muted font-mono">{sub}</div>
      </div>
    </div>
  );
}
