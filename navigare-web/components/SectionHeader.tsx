interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export default function SectionHeader({ title, subtitle, className = "" }: SectionHeaderProps) {
  return (
    <div className={`flex items-center gap-3 mt-6 mb-4 ${className}`}>
      <span className="label-mono text-[10px] font-black text-teal whitespace-nowrap">
        {"/// "}{title}
      </span>
      {subtitle && <span className="text-[10px] text-muted hidden sm:block font-mono">{subtitle}</span>}
      <span className="flex-1 h-[2px] bg-border"></span>
    </div>
  );
}
