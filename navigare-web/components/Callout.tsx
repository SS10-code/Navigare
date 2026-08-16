import { ReactNode } from "react";

type Variant = "info" | "warn" | "good" | "danger";

const VARIANT_STYLES: Record<Variant, { bg: string; border: string; text: string }> = {
  info:  { bg: "bg-paper", border: "border-l-4 border-l-ink", text: "text-ink" },
  warn:  { bg: "bg-paper", border: "border-l-4 border-l-accent", text: "text-accent" },
  good:  { bg: "bg-paper", border: "border-l-4 border-l-accent", text: "text-accent" },
  danger:{ bg: "bg-paper", border: "border-l-4 border-l-accent", text: "text-accent" },
};

interface CalloutProps {
  children: ReactNode;
  variant?: Variant;
  className?: string;
}

export default function Callout({ children, variant = "info", className = "" }: CalloutProps) {
  const style = VARIANT_STYLES[variant];

  return (
    <div
      className={`
        ${style.bg} ${style.text}
        ${style.border} border-r-2 border-t-2 border-b-2
        px-5 py-4
        text-sm leading-relaxed font-medium
        ${className}
      `}
    >
      {children}
    </div>
  );
}
