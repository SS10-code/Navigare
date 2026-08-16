import { ReactNode } from "react";

type Variant = "info" | "warn" | "good" | "danger";

const VARIANT_STYLES: Record<Variant, { bg: string; border: string; text: string }> = {
  info:  { bg: "bg-[#1B1730]", border: "border-purple", text: "text-purple" },
  warn:  { bg: "bg-[#2A2105]", border: "border-amber", text: "text-amber" },
  good:  { bg: "bg-[#04281A]", border: "border-green", text: "text-green" },
  danger:{ bg: "bg-[#2E0A10]", border: "border-red", text: "text-red" },
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
        border-2 ${style.border}
        px-4 py-3
        text-[13px] leading-relaxed font-medium
        ${className}
      `}
    >
      {children}
    </div>
  );
}
