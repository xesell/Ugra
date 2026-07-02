import { Loader2 } from "lucide-react";

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-[var(--text-muted)]">
      <Loader2 className="h-5 w-5 animate-spin text-accent" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
