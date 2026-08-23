import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
  hover?: boolean;
  accent?: boolean;
}

export default function Card({ children, className = "", padding = "lg", hover = false, accent = false }: CardProps) {
  const paddingClasses = {
    sm: "p-4",
    md: "p-5",
    lg: "p-6",
  };

  return (
    <div
      className={`
        bg-panel border-2 border-border
        ${accent ? "border-l-4 border-l-accent" : ""}
        ${paddingClasses[padding]}
        ${hover ? "hover:border-accent hover:shadow-[4px_4px_0_0_rgba(224,69,0,0.15)] transition-all cursor-pointer" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
