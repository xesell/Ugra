import { useEffect, useState } from "react";
import { CheckCircle2, RefreshCw, XCircle } from "lucide-react";
import { api } from "@/api/client";
import { Spinner } from "@/components/ui/Spinner";
import type { SourceInfo } from "@/types";
import { formatDate } from "@/lib/utils";

export function SourcesPage() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.sources().then((d) => {
      setSources(d.sources);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spinner label="Загрузка источников..." />;

  return (
    <div className="space-y-6">
      <div className="page-header">
        <h1>Источники</h1>
        <p>Подключённые площадки поиска вакансий</p>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {sources.map((src) => (
          <div key={src.id} className="card p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{src.name}</h3>
              {src.connected ? (
                <CheckCircle2 className="h-5 w-5 text-success" />
              ) : (
                <XCircle className="h-5 w-5 text-[var(--text-muted)]" />
              )}
            </div>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              {src.connected ? "Подключено" : "Не подключено"}
            </p>
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Синхронизация</span>
                <span>{src.last_sync ? formatDate(src.last_sync) : "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Токен до</span>
                <span>{src.token_expires ?? "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Вакансий</span>
                <span>{src.vacancies_found}</span>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              {src.connected ? (
                <>
                  <button type="button" className="btn-secondary flex-1 text-xs">
                    <RefreshCw className="h-3 w-3" />
                    Обновить
                  </button>
                  <button className="btn-ghost flex-1 border border-surface-border text-xs text-danger">
                    Отключить
                  </button>
                </>
              ) : (
                <button className="btn-primary w-full text-xs">Подключить</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
