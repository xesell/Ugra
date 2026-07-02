import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Briefcase,
  Mail,
  Send,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import { api, subscribeTimeline } from "@/api/client";
import { RecruiterCard } from "@/components/ugra/RecruiterCard";
import {
  type AgentState,
  MASCOT_STATES,
  resolveAgentState,
} from "@/components/ugra/mascotConfig";
import { DashboardSkeleton } from "@/components/ui/Skeleton";
import type { DashboardStats, TimelineEntry } from "@/types";

const statCards = [
  { key: "found" as const, label: "Найдено вакансий", icon: Briefcase },
  { key: "suitable" as const, label: "Подходящих", icon: Target },
  { key: "applied" as const, label: "Откликов", icon: Send },
  { key: "responses" as const, label: "Ответов", icon: Mail },
  { key: "invites" as const, label: "Приглашений", icon: Users },
  { key: "errors" as const, label: "Ошибок", icon: AlertTriangle, isError: true },
];

function deriveFromTimeline(entries: TimelineEntry[]): {
  state: AgentState;
  message: string;
  source: string;
  progress: number | null;
} {
  if (entries.length === 0) {
    return {
      state: "idle",
      message: MASCOT_STATES.idle.messages[0],
      source: "",
      progress: null,
    };
  }

  const latest = entries[0];
  const state = resolveAgentState(latest.event_type, latest.title, latest.detail);
  const message = latest.detail || latest.title;
  const source = latest.source || "";

  let progress: number | null = null;
  if (state === "fitAssessment" && latest.detail) {
    const match = latest.detail.match(/(\d+)%/);
    if (match) progress = Number(match[1]);
  }

  return { state, message, source, progress };
}

function relativeTime(time: string): string {
  return time || "только что";
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [agentState, setAgentState] = useState<AgentState>("idle");
  const [mascotMessage, setMascotMessage] = useState("");
  const [mascotSource, setMascotSource] = useState("");
  const [mascotProgress, setMascotProgress] = useState<number | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const prevTimelineId = useRef<string | null>(null);

  const applyTimeline = (entries: TimelineEntry[]) => {
    setTimeline(entries);
    const derived = deriveFromTimeline(entries);
    setAgentState(derived.state);
    setMascotMessage(derived.message);
    setMascotSource(derived.source);
    setMascotProgress(derived.progress);

    const latestId = entries[0]?.id ?? null;
    if (latestId && latestId !== prevTimelineId.current) {
      prevTimelineId.current = latestId;
      setHighlightedId(latestId);
      setTimeout(() => setHighlightedId(null), 2000);
    }
  };

  useEffect(() => {
    api.dashboard().then((d) => {
      setStats(d.stats);
      applyTimeline(d.timeline);
      setLoading(false);
    });

    const unsub = subscribeTimeline((data) => {
      if (data.timeline) applyTimeline(data.timeline);
      if (data.stats) setStats(data.stats);
    });
    return unsub;
  }, []);

  if (loading || !stats) return <DashboardSkeleton />;

  return (
    <div className="space-y-8">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Текущее состояние работы агента</p>
      </div>

      <RecruiterCard
        state={agentState}
        message={mascotMessage}
        source={mascotSource}
        progress={mascotProgress}
      />

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-3 2xl:grid-cols-6">
        {statCards.map(({ key, label, icon: Icon, isError }) => (
          <div key={key} className="card flex items-center gap-3 p-3">
            <div
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                isError && stats[key] > 0 ? "bg-red-50 text-danger" : "bg-accent-light text-accent"
              }`}
            >
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="truncate text-xs text-subtitle">{label}</div>
              <div
                className={`text-xl font-bold ${isError && stats[key] > 0 ? "text-danger" : ""}`}
              >
                {stats[key]}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <div className="mb-6 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-accent" />
          <div>
            <h2 className="font-semibold">Timeline активности</h2>
            <p className="text-sm text-subtitle">События синхронизированы с Ugra</p>
          </div>
        </div>

        {timeline.length === 0 ? (
          <p className="py-8 text-center text-sm text-subtitle">
            Событий пока нет. Запустите поиск вакансий.
          </p>
        ) : (
          <div className="relative space-y-0 pl-5">
            <div className="absolute bottom-3 left-[7px] top-3 w-px bg-accent/25" />
            {timeline.map((entry, index) => (
              <div
                key={entry.id}
                className={`relative pb-6 transition-colors duration-500 last:pb-0 ${
                  highlightedId === entry.id ? "opacity-100" : ""
                }`}
              >
                <div
                  className={`absolute left-0 top-4 z-10 h-3.5 w-3.5 rounded-full border-2 ${
                    index === 0
                      ? "border-accent bg-accent"
                      : "border-accent/40 bg-white dark:bg-[var(--surface-elevated)]"
                  }`}
                />
                <div
                  className={`ml-6 rounded-xl border px-4 py-3 transition-colors ${
                    highlightedId === entry.id
                      ? "border-accent/30 bg-accent-light"
                      : "border-surface-border bg-surface hover:bg-accent-light/50"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="font-medium">{entry.title}</div>
                    <span className="text-xs text-subtitle">{relativeTime(entry.time)}</span>
                  </div>
                  {entry.detail && (
                    <p className="mt-1 text-sm text-subtitle">{entry.detail}</p>
                  )}
                  {entry.source && (
                    <span className="mt-2 inline-block rounded-md bg-accent-light px-2 py-0.5 text-xs font-medium text-accent-text">
                      {entry.source}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
