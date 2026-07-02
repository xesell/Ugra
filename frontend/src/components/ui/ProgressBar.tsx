import { cn } from "@/lib/utils";

export function ProgressBar({ value, className }: { value: number; className?: string }) {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="w-10 text-right text-sm font-medium">{Math.round(clamped)}%</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-border">
        <div
          className="h-full rounded-full bg-accent transition-all duration-500"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
