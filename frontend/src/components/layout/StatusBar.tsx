import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { SystemStatus } from "@/types";

function StatusDot({ ok, brand }: { ok: boolean; brand?: boolean }) {
  return (
    <span
      className={`inline-block h-2 w-2 shrink-0 rounded-full ${
        brand ? "bg-accent" : ok ? "bg-success" : "bg-danger"
      }`}
      aria-hidden
    />
  );
}

export function StatusBar() {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const load = () => api.status().then(setStatus).catch(() => {});
    load();
    const id = setInterval(load, 10000);
    return () => clearInterval(id);
  }, []);

  if (!status) return null;

  const hhOk = status.sources.hh === "connected";
  const geekOk = status.sources.geekjob === "connected";
  const tgOk = status.telegram === "online";

  const items = [
    { dot: <StatusDot ok={hhOk} />, label: "HH", value: hhOk ? "Online" : "Offline" },
    { dot: <StatusDot ok={geekOk} />, label: "GeekJob", value: geekOk ? "Online" : "Offline" },
    { dot: <StatusDot ok={tgOk} />, label: "Telegram", value: tgOk ? "Online" : "Offline" },
    { dot: <StatusDot ok brand />, label: status.llm.model, value: status.llm.provider },
    { dot: null, label: "CPU", value: `${status.cpu_percent}%` },
    { dot: null, label: "RAM", value: `${status.ram_gb} GB` },
    { dot: null, label: "Sync", value: status.last_sync },
  ];

  return (
    <footer className="flex h-10 shrink-0 items-center gap-0 border-t border-surface-border bg-[var(--sidebar)] px-5 text-xs text-subtitle">
      {items.map((item, i) => (
        <div key={item.label} className="flex items-center">
          {i > 0 && <span className="mx-4 h-3 w-px bg-surface-border" aria-hidden />}
          <div className="flex items-center gap-2">
            {item.dot}
            <span className="font-medium text-[var(--text)]">{item.label}</span>
            <span>{item.value}</span>
          </div>
        </div>
      ))}
      {status.agent_mood && (
        <>
          <span className="mx-4 h-3 w-px bg-surface-border" aria-hidden />
          <span className="text-accent-text">{status.agent_mood}</span>
        </>
      )}
    </footer>
  );
}
