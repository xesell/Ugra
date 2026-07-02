import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import { api } from "@/api/client";
import { Spinner } from "@/components/ui/Spinner";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Application } from "@/types";
import { formatDate } from "@/lib/utils";

export function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [selected, setSelected] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.applications().then((d) => {
      setApps(d.applications);
      setLoading(false);
    });
    const id = setInterval(() => api.applications().then((d) => setApps(d.applications)), 15000);
    return () => clearInterval(id);
  }, []);

  const filtered = apps.filter(
    (a) =>
      !filter ||
      a.company.toLowerCase().includes(filter.toLowerCase()) ||
      a.title.toLowerCase().includes(filter.toLowerCase()),
  );

  if (loading) return <Spinner label="Загрузка откликов..." />;

  return (
    <div className="flex h-full gap-4">
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="page-header">
            <h1>Отклики</h1>
            <p>{filtered.length} записей</p>
          </div>
          <input
            className="input w-64"
            placeholder="Поиск..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>

        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-surface-elevated">
              <tr>
                {["Компания", "Вакансия", "Когда отправлено", "Источник", "Статус", "Изменение"].map(
                  (h) => (
                    <th key={h} className="table-cell table-head">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="table-cell text-center text-[var(--text-muted)]">
                    Откликов пока нет. Отправьте отклик из раздела «Поиск вакансий».
                  </td>
                </tr>
              ) : (
                filtered.map((app) => (
                  <tr
                    key={app.id}
                    className={`table-row cursor-pointer ${selected?.id === app.id ? "table-row-selected" : ""}`}
                    onClick={() => setSelected(app)}
                  >
                    <td className="table-cell">{app.company}</td>
                    <td className="table-cell">{app.title}</td>
                    <td className="table-cell text-[var(--text-muted)]">{formatDate(app.sent_at)}</td>
                    <td className="table-cell">{app.source}</td>
                    <td className="table-cell">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="table-cell text-[var(--text-muted)]">{formatDate(app.updated_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selected && (
        <aside className="card w-96 shrink-0 overflow-auto p-4">
          <h2 className="text-lg font-semibold">{selected.title}</h2>
          <p className="text-sm text-[var(--text-muted)]">{selected.company}</p>
          {selected.url && (
            <a
              href={selected.url}
              target="_blank"
              rel="noreferrer"
              className="btn-ghost mt-2 text-accent"
            >
              <ExternalLink className="h-4 w-4" />
              Открыть вакансию
            </a>
          )}

          <div className="mt-4 space-y-3 text-sm">
            <div>
              <div className="text-xs text-[var(--text-muted)]">Резюме</div>
              <div>{selected.resume_title || "—"}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--text-muted)]">Сопроводительное</div>
              <div className="whitespace-pre-wrap text-[var(--text-muted)]">
                {selected.cover_letter_preview || "—"}
              </div>
            </div>
            <div>
              <div className="text-xs text-[var(--text-muted)]">История действий</div>
              <ul className="mt-1 space-y-1">
                {selected.history.map((h, i) => (
                  <li key={i} className="text-[var(--text-muted)]">
                    <span className="font-mono text-xs">{formatDate(h.time)}</span> — {h.action}
                  </li>
                ))}
              </ul>
            </div>
            {selected.employer_reply && (
              <div>
                <div className="text-xs text-[var(--text-muted)]">Ответ работодателя</div>
                <div>{selected.employer_reply}</div>
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
