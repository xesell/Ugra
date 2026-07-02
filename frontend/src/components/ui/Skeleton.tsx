import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} aria-hidden />;
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="page-header space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-5 w-72" />
      </div>

      {/* Recruiter card skeleton */}
      <div className="overflow-hidden rounded-mascot border border-accent/10 bg-gradient-to-b from-white to-[#FAF8FF] p-8 shadow-card">
        <div className="flex gap-8">
          <Skeleton className="h-[280px] w-[240px] shrink-0 rounded-mascot" />
          <div className="flex flex-1 flex-col justify-center gap-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-20 w-full max-w-lg rounded-xl" />
            <Skeleton className="h-2 w-full max-w-md rounded-full" />
          </div>
        </div>
      </div>

      {/* Stats skeleton */}
      <div className="grid grid-cols-3 gap-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card flex items-center gap-3 p-3">
            <Skeleton className="h-8 w-8 shrink-0 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-6 w-10" />
            </div>
          </div>
        ))}
      </div>

      {/* Timeline skeleton */}
      <div className="card p-6">
        <Skeleton className="mb-6 h-5 w-48" />
        <div className="relative space-y-6 pl-6">
          <div className="absolute bottom-2 left-[7px] top-2 w-px bg-accent/20" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="relative flex gap-4">
              <Skeleton className="relative z-10 h-3.5 w-3.5 shrink-0 rounded-full" />
              <div className="flex-1 space-y-2 rounded-xl border border-surface-border bg-surface p-4">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
