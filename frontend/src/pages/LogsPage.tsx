import { useCallback, useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { api } from "@/api/client";
import { Spinner } from "@/components/ui/Spinner";
import type { LogEntry } from "@/types";
import { formatDate } from "@/lib/utils";

const levels = ["", "INFO", "WARNING", "ERROR", "DEBUG"];

export function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [level, setLevel] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const load = useCallback(() => {
    api.logs(level || undefined, search || undefined).then((d) => {
      setLogs(d.logs);
      setLoading(false);
    });
  }, [level, search]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [autoRefresh, load]);

  const exportLogs = () => {
    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ugra-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const levelColor: Record<string, string> = {
    INFO: "text-accent",
    WARNING: "text-warning",
    ERROR: "text-danger",
    DEBUG: "text-[var(--text-muted)]",
  };

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="page-header">
          <h1>Логи</h1>
          <p>{logs.length} записей</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input w-32" value={level} onChange={(e) => setLevel(e.target.value)}>
            {levels.map((l) => (
              <option key={l} value={l}>
                {l || "Все"}
              </option>
            ))}
          </select>
          <input
            className="input w-48"
            placeholder="Поиск..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <label className="flex items-center gap-1 text-sm text-[var(--text-muted)]">
            <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
            Авто
          </label>
          <button className="btn-ghost border border-surface-border" onClick={load}>
            <RefreshCw className="h-4 w-4" />
          </button>
          <button className="btn-ghost border border-surface-border" onClick={exportLogs}>
            <Download className="h-4 w-4" />
            Экспорт
          </button>
        </div>
      </div>

      {loading && logs.length === 0 ? (
        <Spinner label="Загрузка логов..." />
      ) : (
        <div className="card flex-1 overflow-auto">
          <table className="w-full">
            <thead className="sticky top-0 bg-surface-elevated">
              <tr>
                {["Время", "Уровень", "Сервис", "Сообщение"].map((h) => (
                  <th key={h} className="table-cell table-head">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-surface-hover">
                  <td className="table-cell whitespace-nowrap font-mono text-xs text-[var(--text-muted)]">
                    {formatDate(log.time)}
                  </td>
                  <td className={`table-cell font-medium ${levelColor[log.level] ?? ""}`}>{log.level}</td>
                  <td className="table-cell">{log.service}</td>
                  <td className="table-cell">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
