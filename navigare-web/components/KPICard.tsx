type Accent = "teal" | "green" | "purple" | "amber" | "red" | "blue" | "magenta";

const ACCENT_COLORS: Record<Accent, string> = {
  teal: "#00FFC8",
  green: "#00E676",
  purple: "#7C5CFF",
  amber: "#FFB800",
  red: "#FF3B3B",
  blue: "#4DA3FF",
  magenta: "#FF2E88",
};

interface Props {
  label: string;
  value: string;
  sub: string;
  accent?: Accent;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}

export default function KPICard({ label, value, sub, accent = "teal", icon, trend }: Props) {
  const color = ACCENT_COLORS[accent];
  return (
    <div
      className="bg-panel border-2 border-border p-5 relative overflow-hidden animate-fade-in card-hover"
      style={{ boxShadow: `5px 5px 0 0 ${color}33` }}
    >
      <div
        className="absolute top-0 left-0 h-[3px] w-full"
        style={{ background: color }}
      />
      <div className="relative">
        <div className="flex items-center justify-between mb-2">
          <div className="label-mono text-[10px] font-bold text-muted">{label}</div>
          {icon && <div style={{ color }}>{icon}</div>}
        </div>
        <div className="text-3xl font-black text-text font-mono tracking-tight">{value}</div>
        <div className="flex items-center gap-1 mt-1.5">
          {trend === "up" && <span className="text-green text-xs font-bold">↑</span>}
          {trend === "down" && <span className="text-red text-xs font-bold">↓</span>}
          <div className="text-[11px] text-muted font-mono">{sub}</div>
        </div>
      </div>
    </div>
  );
}
