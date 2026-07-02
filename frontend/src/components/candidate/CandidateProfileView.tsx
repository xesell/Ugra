import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  Clock,
  Eye,
  FileText,
  Pencil,
  RefreshCw,
  Star,
  Upload,
  X,
} from "lucide-react";
import { api } from "@/api/client";
import type { CandidateProfile, EmployerPreview, ProfileHistoryEntry } from "@/types";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function starCount(years: number): number {
  if (years >= 5) return 5;
  if (years >= 3) return 4;
  if (years >= 1.5) return 3;
  if (years >= 0.5) return 2;
  return years > 0 ? 1 : 0;
}

function Stars({ value }: { value: number }) {
  return (
    <span className="tracking-wider text-amber-400">
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={i < value ? "opacity-100" : "opacity-25"}>
          ★
        </span>
      ))}
    </span>
  );
}

function getAiSummary(profile: CandidateProfile): string[] {
  if (profile.ai_summary?.length) return profile.ai_summary;
  const lines = [
    `Основная специализация — ${profile.identity.primary_specialization}.`,
    profile.identity.level_rationale,
    ...profile.strengths.slice(0, 6),
  ].filter(Boolean);
  return lines;
}

type EditField = "specialization" | "level" | "roles" | null;

interface CandidateProfileViewProps {
  profile: CandidateProfile;
  onProfileUpdate: (profile: CandidateProfile) => void;
  onReupload: () => void;
  onRescan: () => void;
}

export function CandidateProfileView({
  profile,
  onProfileUpdate,
  onReupload,
  onRescan,
}: CandidateProfileViewProps) {
  const [tab, setTab] = useState<"profile" | "history">("profile");
  const [history, setHistory] = useState<ProfileHistoryEntry[]>([]);
  const [employerPreview, setEmployerPreview] = useState<EmployerPreview | null>(null);
  const [previewModal, setPreviewModal] = useState<"resume" | "cover" | "match" | null>(null);
  const [editField, setEditField] = useState<EditField>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);

  const loadHistory = useCallback(async () => {
    const data = await api.profileHistory();
    setHistory(data.history);
  }, []);

  const loadEmployerPreview = useCallback(async () => {
    try {
      const data = await api.employerPreview();
      setEmployerPreview(data);
    } catch {
      setEmployerPreview(null);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
    void loadEmployerPreview();
  }, [profile.version, loadHistory, loadEmployerPreview]);

  const highRoles = profile.preferred_roles.filter((r) => r.priority === "high");
  const mediumRoles = profile.preferred_roles.filter((r) => r.priority === "medium");
  const lowRoles = profile.preferred_roles.filter((r) => r.priority === "low");
  const excluded =
    profile.search_strategy.excluded_roles.length > 0
      ? profile.search_strategy.excluded_roles
      : profile.search_strategy.exclude_keywords;

  const topSkills = [...profile.skills].sort((a, b) => b.confidence - a.confidence).slice(0, 16);
  const expYears = profile.experience.commercial_years || profile.experience.total_years;
  const meta = profile.analysis_meta ?? {
    model: "—",
    provider: "",
    duration_seconds: 0,
    resume_filename: "",
  };
  const stats = profile.analysis_stats ?? {
    skills_count: profile.skills.length,
    technologies_count: profile.skills.length,
    companies_count: 0,
    projects_count: 0,
    domains_count: profile.domains.length,
    roles_count: profile.preferred_roles.length,
  };

  const saveEdit = async () => {
    if (!editField) return;
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {};
      if (editField === "specialization") payload.primary_specialization = editValue;
      if (editField === "level") payload.level = editValue;
      const { profile: updated } = await api.updateCandidateProfile(payload);
      onProfileUpdate(updated);
      setEditField(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const competencyRows = [
    { label: "Архитектура", years: profile.experience.architecture_years },
    { label: "Backend", years: profile.experience.backend_years },
    { label: "AI", years: profile.experience.ai_years },
    { label: "DevOps", years: profile.experience.devops_years },
    { label: "Leadership", years: profile.experience.leadership_years },
  ].filter((r) => r.years > 0);

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-12">
      <div className="flex items-start justify-between gap-4">
        <div className="page-header">
          <h1>Профиль кандидата</h1>
          <p>Внутренний профиль Ugra — основа поиска вакансий и откликов</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button type="button" className="btn-secondary" onClick={onRescan}>
            <RefreshCw className="h-4 w-4" />
            Пересканировать
          </button>
          <button type="button" className="btn-primary" onClick={onReupload}>
            <Upload className="h-4 w-4" />
            Загрузить новое PDF
          </button>
        </div>
      </div>

      <div className="flex gap-1 border-b border-surface-border">
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${tab === "profile" ? "border-b-2 border-accent text-accent" : "text-[var(--text-muted)]"}`}
          onClick={() => setTab("profile")}
        >
          Профиль
        </button>
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${tab === "history" ? "border-b-2 border-accent text-accent" : "text-[var(--text-muted)]"}`}
          onClick={() => setTab("history")}
        >
          История анализа
        </button>
      </div>

      {tab === "history" ? (
        <div className="card divide-y divide-surface-border">
          {history.length === 0 ? (
            <p className="p-6 text-sm text-[var(--text-muted)]">История пока пуста</p>
          ) : (
            history.map((entry) => (
              <div key={`${entry.version}-${entry.analyzed_at}`} className="flex gap-4 p-4 text-sm">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-light text-accent">
                  v{entry.version}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{formatDate(entry.analyzed_at)}</div>
                  <div className="mt-1 text-[var(--text-muted)]">
                    Модель: {entry.model || "—"} · {entry.duration_seconds.toFixed(1)} сек
                  </div>
                  <div className="mt-1">{entry.changes_summary}</div>
                  <div className="mt-1 text-xs text-[var(--text-muted)]">{entry.trigger}</div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <>
          {/* 1. Статус анализа */}
          <section className="card border-success/30 bg-success/5 p-6">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-6 w-6 shrink-0 text-success" />
              <div className="flex-1">
                <h2 className="font-semibold text-success">Профиль успешно сформирован</h2>
                <dl className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <dt className="text-[var(--text-muted)]">Последний анализ</dt>
                    <dd className="mt-1 font-medium">{formatDate(profile.analyzed_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--text-muted)]">Используемая модель</dt>
                    <dd className="mt-1 font-medium">{meta.model}</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--text-muted)]">Версия профиля</dt>
                    <dd className="mt-1 font-medium">v{profile.version}</dd>
                  </div>
                </dl>
                {meta.resume_filename && (
                  <p className="mt-3 text-xs text-[var(--text-muted)]">
                    Файл: {meta.resume_filename}
                    {meta.duration_seconds > 0 && (
                      <span className="ml-2 inline-flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {meta.duration_seconds.toFixed(1)} сек
                      </span>
                    )}
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* 2. Что AI поняла */}
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-semibold">Что AI поняла о вас</h2>
            <p className="mb-3 text-sm text-[var(--text-muted)]">
              На основании анализа вашего резюме я определила:
            </p>
            <ul className="space-y-2 text-sm leading-relaxed">
              {getAiSummary(profile).map((line) => (
                <li key={line} className="flex gap-2">
                  <span className="text-accent">•</span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* 3. Профессиональный профиль */}
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-semibold">Итоговый профессиональный профиль</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <ProfileCard
                label="Основная роль"
                value={profile.identity.primary_specialization}
                onEdit={() => {
                  setEditField("specialization");
                  setEditValue(profile.identity.primary_specialization);
                }}
              />
              <ProfileCard
                label="Уровень"
                value={profile.identity.level.charAt(0).toUpperCase() + profile.identity.level.slice(1)}
                onEdit={() => {
                  setEditField("level");
                  setEditValue(profile.identity.level);
                }}
              />
              <ProfileCard label="Опыт" value={`${Math.round(expYears)} лет`} />
            </div>
            {competencyRows.length > 0 && (
              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
                {competencyRows.map((row) => (
                  <div
                    key={row.label}
                    className="flex items-center justify-between rounded-md border border-surface-border px-3 py-2 text-sm"
                  >
                    <span>{row.label}</span>
                    <Stars value={starCount(row.years)} />
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* 4. Что будет искать агент */}
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-semibold">Что будет искать агент</h2>
            <div className="space-y-4 text-sm">
              {highRoles.length > 0 && (
                <PriorityBlock title="Высокий приоритет" stars={5} items={highRoles.map((r) => r.title)} />
              )}
              {mediumRoles.length > 0 && (
                <PriorityBlock
                  title="Средний приоритет"
                  stars={3}
                  items={mediumRoles.map((r) => r.title)}
                />
              )}
              {lowRoles.length > 0 && (
                <PriorityBlock title="Низкий приоритет" stars={1} items={lowRoles.map((r) => r.title)} />
              )}
              {excluded.length > 0 && (
                <div>
                  <div className="mb-2 font-medium text-danger">Не искать</div>
                  <div className="flex flex-wrap gap-2">
                    {excluded.map((item) => (
                      <span
                        key={item}
                        className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-400"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* 5. Ключевые технологии */}
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-semibold">Ключевые технологии</h2>
            <div className="flex flex-wrap gap-2">
              {topSkills.map((skill) => (
                <span
                  key={skill.name}
                  className="inline-flex items-center gap-2 rounded-full border border-surface-border px-3 py-1 text-sm"
                  title={`Уверенность: ${Math.round(skill.confidence)}%`}
                >
                  {skill.name}
                  <span className="text-xs text-[var(--text-muted)]">
                    {Math.round(skill.confidence)}%
                  </span>
                </span>
              ))}
            </div>
          </section>

          {/* 6. Доменная экспертиза */}
          {profile.domains.length > 0 && (
            <section className="card p-6">
              <h2 className="mb-4 text-lg font-semibold">Доменная экспертиза</h2>
              <div className="flex flex-wrap gap-2">
                {profile.domains.map((d) => (
                  <span key={d} className="rounded-md bg-accent-light px-3 py-1.5 text-sm text-accent-text">
                    {d}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* 7. Что отправляется работодателю */}
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-semibold">Что будет отправляться работодателю</h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <PreviewButton
                icon={FileText}
                label="Резюме"
                sub={meta.resume_filename || "PDF"}
                onClick={() => setPreviewModal("resume")}
              />
              <PreviewButton
                icon={Eye}
                label="Сопроводительное письмо"
                sub="Предпросмотр"
                onClick={() => setPreviewModal("cover")}
              />
              <PreviewButton
                icon={Star}
                label="Причина выбора вакансии"
                sub="Показать"
                onClick={() => setPreviewModal("match")}
              />
            </div>
          </section>

          {/* 8. Внутренние выводы AI */}
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-semibold">Внутренние выводы AI</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <StatCard label="Извлечено навыков" value={stats.skills_count} />
              <StatCard label="Компаний" value={stats.companies_count} />
              <StatCard label="Проектов" value={stats.projects_count} />
              <StatCard label="Технологий" value={stats.technologies_count} />
              <StatCard label="Доменных областей" value={stats.domains_count} />
              <StatCard label="Карьерных ролей" value={stats.roles_count} />
            </div>
          </section>
        </>
      )}

      {editField && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="card w-full max-w-md p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold">Исправить</h3>
              <button type="button" className="btn-ghost p-1" onClick={() => setEditField(null)}>
                <X className="h-4 w-4" />
              </button>
            </div>
            {editField === "level" ? (
              <select
                className="input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
              >
                {["junior", "middle", "senior", "lead", "architect"].map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
              />
            )}
            <p className="mt-2 text-xs text-[var(--text-muted)]">
              После сохранения профиль и поисковая стратегия обновятся для всех AI-запросов.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="btn-ghost" onClick={() => setEditField(null)}>
                Отмена
              </button>
              <button type="button" className="btn-primary" disabled={saving} onClick={() => void saveEdit()}>
                {saving ? "Сохранение…" : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      )}

      {previewModal && employerPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="card max-h-[80vh] w-full max-w-2xl overflow-hidden shadow-xl">
            <div className="flex items-center justify-between border-b border-surface-border p-4">
              <h3 className="font-semibold">
                {previewModal === "resume" && "Резюме"}
                {previewModal === "cover" && "Сопроводительное письмо"}
                {previewModal === "match" && "Причина выбора вакансии"}
              </h3>
              <button type="button" className="btn-ghost p-1" onClick={() => setPreviewModal(null)}>
                <X className="h-4 w-4" />
              </button>
            </div>
            <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap p-4 text-sm leading-relaxed">
              {previewModal === "resume" &&
                (employerPreview.resume_excerpt || "Текст резюме недоступен")}
              {previewModal === "cover" && employerPreview.cover_letter}
              {previewModal === "match" &&
                (employerPreview.match_rationale.length
                  ? employerPreview.match_rationale.map((r) => `• ${r}`).join("\n")
                  : "Нет данных")}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileCard({
  label,
  value,
  onEdit,
}: {
  label: string;
  value: string;
  onEdit?: () => void;
}) {
  return (
    <div className="rounded-lg border border-surface-border p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs text-[var(--text-muted)]">{label}</div>
        {onEdit && (
          <button type="button" className="text-[var(--text-muted)] hover:text-accent" onClick={onEdit}>
            <Pencil className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
      <div className="mt-2 font-medium">{value}</div>
    </div>
  );
}

function PriorityBlock({
  title,
  stars,
  items,
}: {
  title: string;
  stars: number;
  items: string[];
}) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 font-medium">
        {title}
        <span className="text-amber-400 text-xs">{"★".repeat(stars)}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded-full bg-surface-border px-3 py-1 text-xs">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-surface-border p-4 text-center">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-[var(--text-muted)]">{label}</div>
    </div>
  );
}

function PreviewButton({
  icon: Icon,
  label,
  sub,
  onClick,
}: {
  icon: typeof FileText;
  label: string;
  sub: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="flex flex-col items-start gap-2 rounded-lg border border-surface-border p-4 text-left transition-colors hover:border-accent/50 hover:bg-accent/5"
      onClick={onClick}
    >
      <Icon className="h-5 w-5 text-accent" />
      <div className="font-medium">{label}</div>
      <div className="text-xs text-accent">{sub}</div>
    </button>
  );
}
