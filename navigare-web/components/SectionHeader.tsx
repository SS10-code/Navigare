interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export default function SectionHeader({ title, subtitle, className = "" }: SectionHeaderProps) {
  return (
    <div className={`flex items-center gap-4 mb-6 ${className}`}>
      <span className="text-caption text-ink text-[11px] font-bold tracking-wider">
        {title}
      </span>
      {subtitle && <span className="text-caption text-muted text-[10px]">{subtitle}</span>}
      <span className="flex-1 h-[2px] bg-border"></span>
    </div>
  );
}
