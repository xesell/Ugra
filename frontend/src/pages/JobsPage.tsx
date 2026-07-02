import { Fragment, useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink, RefreshCw, Search, X } from "lucide-react";
import { api } from "@/api/client";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Spinner } from "@/components/ui/Spinner";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/stores/toast";
import type { Job } from "@/types";
import { formatDate } from "@/lib/utils";

interface Filters {
  salary_min: string;
  technologies: string;
  experience_years: string;
  remote_only: boolean;
  level: string;
  country: string;
  keywords: string;
  excluded_companies: string;
}

const defaultFilters: Filters = {
  salary_min: "",
  technologies: "",
  experience_years: "3",
  remote_only: false,
  level: "",
  country: "",
  keywords: "",
  excluded_companies: "",
};

export function JobsPage() {
  const { toast } = useToast();
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<"match_score" | "title" | "company">("match_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const searchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const techs = filters.technologies.split(",").map((s) => s.trim()).filter(Boolean);
      const kws = filters.keywords.split(",").map((s) => s.trim()).filter(Boolean);
      const skills = techs.length ? techs : ["Python", "FastAPI"];
      const result = await api.searchJobs({
        salary_min: filters.salary_min ? Number(filters.salary_min) : "",
        technologies: techs,
        keywords: kws,
        remote_only: filters.remote_only,
        level: filters.level,
        country: filters.country,
        skills,
        experience_years: Number(filters.experience_years) || 0,
      });
      let list = result.jobs;
      if (filters.excluded_companies) {
        const excluded = filters.excluded_companies.split(",").map((s) => s.trim().toLowerCase());
        list = list.filter((j) => !excluded.includes(j.company.toLowerCase()));
      }
      setJobs(list);
      toast(`Найдено ${list.length} вакансий`, "success");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Ошибка поиска", "error");
    } finally {
      setLoading(false);
    }
  }, [filters, toast]);

  useEffect(() => {
    searchJobs();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "f") {
        e.preventDefault();
        document.getElementById("job-search")?.focus();
      }
      if (e.ctrlKey && e.key === "r") {
        e.preventDefault();
        searchJobs();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [searchJobs]);

  const filtered = jobs
    .filter(
      (j) =>
        !search ||
        j.title.toLowerCase().includes(search.toLowerCase()) ||
        j.company.toLowerCase().includes(search.toLowerCase()),
    )
    .sort((a, b) => {
      const av = a[sortKey] as string | number;
      const bv = b[sortKey] as string | number;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });

  const toggleSort = (key: typeof sortKey) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const handleApply = async (job: Job) => {
    try {
      await api.apply(job);
      toast(`Отклик на «${job.title}» отправлен`, "success");
    } catch {
      toast("Не удалось отправить отклик", "error");
    }
  };

  const handleIgnore = async (job: Job) => {
    await api.ignoreJob(job.id);
    setJobs((j) => j.filter((x) => x.id !== job.id));
    toast("Вакансия скрыта", "info");
  };

  return (
    <div className="flex h-full gap-4">
      <aside className="card w-64 shrink-0 space-y-3 p-4">
        <h2 className="text-sm font-medium">Фильтры</h2>
        {(
          [
            ["salary_min", "Мин. зарплата", "number"],
            ["technologies", "Стек (через запятую)", "text"],
            ["experience_years", "Опыт (лет)", "number"],
            ["level", "Уровень", "text"],
            ["country", "Страна", "text"],
            ["keywords", "Ключевые слова", "text"],
            ["excluded_companies", "Исключить компании", "text"],
          ] as const
        ).map(([key, label, type]) => (
          <label key={key} className="block text-xs text-[var(--text-muted)]">
            {label}
            <input
              type={type}
              className="input mt-1"
              value={filters[key]}
              onChange={(e) => setFilters((f) => ({ ...f, [key]: e.target.value }))}
            />
          </label>
        ))}
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.remote_only}
            onChange={(e) => setFilters((f) => ({ ...f, remote_only: e.target.checked }))}
          />
          Только удалённо
        </label>
        <button onClick={searchJobs} className="btn-primary w-full" disabled={loading}>
          {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Найти
        </button>
        <p className="text-xs text-[var(--text-muted)]">Ctrl+F — поиск, Ctrl+R — обновить</p>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="page-header">
            <h1>Поиск вакансий</h1>
            <p>{filtered.length} вакансий</p>
          </div>
          <input
            id="job-search"
            className="input w-64"
            placeholder="Поиск по таблице..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {loading && jobs.length === 0 ? (
          <Spinner label="Поиск вакансий..." />
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-surface-elevated">
                <tr>
                  <th className="table-cell w-8" />
                  {[
                    ["source", "Источник"],
                    ["company", "Компания", "company"],
                    ["title", "Вакансия", "title"],
                    ["salary", "Зарплата"],
                    ["match", "Совпадение", "match_score"],
                    ["date", "Дата"],
                    ["status", "Статус"],
                  ].map(([key, label, sort]) => (
                    <th
                      key={key}
                      className={`table-cell table-head ${sort ? "cursor-pointer hover:text-[var(--text)]" : ""}`}
                      onClick={() => sort && toggleSort(sort as typeof sortKey)}
                    >
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((job) => (
                  <Fragment key={job.id}>
                    <tr
                      className={`table-row cursor-pointer ${expanded === job.id ? "table-row-selected" : ""}`}
                      onClick={() => setExpanded(expanded === job.id ? null : job.id)}
                    >
                      <td className="table-cell">
                        {expanded === job.id ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </td>
                      <td className="table-cell font-medium text-accent">{job.source}</td>
                      <td className="table-cell">{job.company}</td>
                      <td className="table-cell">{job.title}</td>
                      <td className="table-cell text-[var(--text-muted)]">—</td>
                      <td className="table-cell">
                        <ProgressBar value={job.match_score} />
                      </td>
                      <td className="table-cell text-[var(--text-muted)]">{formatDate(new Date().toISOString())}</td>
                      <td className="table-cell">
                        <StatusBadge status={job.recommended ? "analyzed" : "new"} />
                      </td>
                    </tr>
                    {expanded === job.id && (
                      <tr>
                        <td colSpan={8} className="border-b border-surface-border bg-surface-elevated px-6 py-4">
                          <div className="grid grid-cols-2 gap-6 text-sm">
                            <div>
                              <h4 className="mb-2 font-medium">Описание</h4>
                              <p className="text-[var(--text-muted)]">
                                {job.description || "Описание загружается из источника при полном анализе."}
                              </p>
                              <h4 className="mb-2 mt-4 font-medium">Причины оценки GPT</h4>
                              <ul className="list-disc pl-4 text-[var(--text-muted)]">
                                {job.pros.map((p) => (
                                  <li key={p} className="text-success">
                                    + {p}
                                  </li>
                                ))}
                                {job.cons.map((c) => (
                                  <li key={c} className="text-danger">
                                    − {c}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <h4 className="mb-2 font-medium">Недостающие навыки</h4>
                              <p className="text-[var(--text-muted)]">
                                {job.skill_gaps.length ? job.skill_gaps.join(", ") : "Нет"}
                              </p>
                              <div className="mt-4 flex gap-2">
                                <button className="btn-primary" onClick={() => handleApply(job)}>
                                  Откликнуться
                                </button>
                                <a
                                  href={job.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="btn-secondary"
                                >
                                  <ExternalLink className="h-4 w-4" />
                                  Открыть
                                </a>
                                <button className="btn-ghost" onClick={() => handleIgnore(job)}>
                                  <X className="h-4 w-4" />
                                  Игнорировать
                                </button>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
