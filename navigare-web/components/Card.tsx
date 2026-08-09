import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
  hover?: boolean;
  accent?: "teal" | "magenta" | "amber" | "none";
}

export default function Card({ children, className = "", padding = "lg", hover = false, accent = "none" }: CardProps) {
  const paddingClasses = {
    sm: "p-4",
    md: "p-5",
    lg: "p-6",
  };

  const accentBorder =
    accent === "teal" ? "border-t-[3px] border-t-teal" :
    accent === "magenta" ? "border-t-[3px] border-t-magenta" :
    accent === "amber" ? "border-t-[3px] border-t-amber" : "";

  return (
    <div
      className={`
        bg-panel border-2 border-border
        animate-fade-in
        ${accentBorder}
        ${paddingClasses[padding]}
        ${hover ? "card-hover cursor-pointer" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
