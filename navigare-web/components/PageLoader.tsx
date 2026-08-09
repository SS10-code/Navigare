import Icon from "@/components/Icon";

export function PageLoader({ message = "LOADING..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 animate-fade-in">
      <div className="w-12 h-12 border-4 border-teal border-t-transparent animate-spin-slow mb-4" />
      <div className="label-mono text-xs text-teal animate-blink">{message}</div>
    </div>
  );
}

export function KPISkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="bg-panel border-2 border-border p-5" style={{ animationDelay: `${i * 100}ms` }}>
          <div className="skeleton h-3 w-20 mb-3" />
          <div className="skeleton h-8 w-20 mb-2" />
          <div className="skeleton h-3 w-24" />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-panel border-2 border-border p-6">
      <div className="skeleton h-4 w-40 mb-6" />
      <div className="skeleton h-full min-h-[200px] w-full" />
    </div>
  );
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
      <Icon name="box" size={56} className="text-muted mb-4" />
      <div className="text-lg font-black text-text uppercase mb-2">{title}</div>
      <div className="text-sm text-muted max-w-sm font-mono">{message}</div>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
      <Icon name="alert" size={56} className="text-red mb-4" />
      <div className="text-lg font-black text-text uppercase mb-2">Something went wrong</div>
      <div className="text-sm text-muted max-w-md mb-4 font-mono">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary text-sm">
          Retry
        </button>
      )}
    </div>
  );
}
