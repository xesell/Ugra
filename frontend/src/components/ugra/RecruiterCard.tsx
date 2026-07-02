import { Mascot } from "./Mascot";
import { type AgentState, MASCOT_STATES, pickMessage } from "./mascotConfig";

interface RecruiterCardProps {
  state: AgentState;
  message?: string;
  source?: string;
  progress?: number | null;
}

export function RecruiterCard({ state, message, source, progress }: RecruiterCardProps) {
  const config = MASCOT_STATES[state];
  const bubbleText = message ?? pickMessage(state);
  const showProgress = config.progress && progress !== null && progress !== undefined;

  return (
    <div className="overflow-hidden rounded-mascot border border-accent/10 bg-gradient-to-b from-white to-[#FAF8FF] shadow-card dark:from-[var(--surface-elevated)] dark:to-[#1a1528]">
      <div className="flex gap-8 p-8">
        {/* Character — lavender frame */}
        <div className="shrink-0 rounded-mascot bg-accent-light/50 p-4 shadow-mascot">
          <Mascot state={state} height={300} className="shrink-0" />
        </div>

        <div className="flex min-w-0 flex-1 flex-col justify-center gap-5">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-accent">
              AI-рекрутер
            </div>
            <h2 className="mt-1 text-3xl font-bold tracking-tight">Ugra</h2>
            <p className="mt-2 text-base font-medium text-[var(--text)]">{config.status}</p>
          </div>

          <div className="relative max-w-xl rounded-xl border border-accent/15 bg-white px-5 py-4 text-sm leading-relaxed shadow-sm dark:bg-[var(--surface)]">
            <div
              className="absolute -left-2 top-8 h-3 w-3 rotate-45 border-b border-l border-accent/15 bg-white dark:bg-[var(--surface)]"
              aria-hidden
            />
            {bubbleText}
          </div>

          {config.progress && (
            <div className="max-w-md space-y-2">
              <div className="flex justify-between text-xs text-subtitle">
                <span>Текущая операция</span>
                {showProgress ? <span className="font-medium text-accent">{Math.round(progress)}%</span> : <span>В процессе…</span>}
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-accent-light">
                {showProgress ? (
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                  />
                ) : (
                  <div className="h-full w-1/3 animate-pulse rounded-full bg-accent/70" />
                )}
              </div>
            </div>
          )}

          {source && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-subtitle">Источник:</span>
              <span className="rounded-lg border border-accent/20 bg-accent-light px-3 py-1 font-medium text-accent-text">
                {source}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
