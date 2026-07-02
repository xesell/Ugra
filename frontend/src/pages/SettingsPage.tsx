import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/stores/toast";
import type { UISettings } from "@/types";

const tabs = [
  { id: "llm", label: "LLM" },
  { id: "search", label: "Поиск" },
  { id: "auto", label: "Автоотклик" },
  { id: "telegram", label: "Telegram" },
  { id: "proxy", label: "Proxy" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function SettingsPage() {
  const { toast } = useToast();
  const [tab, setTab] = useState<TabId>("llm");
  const [settings, setSettings] = useState<UISettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.settings().then((s) => {
      setSettings(s);
      setLoading(false);
    });
  }, []);

  const save = async () => {
    if (!settings) return;
    try {
      const updated = await api.updateSettings(settings);
      setSettings(updated);
      toast("Настройки сохранены", "success");
    } catch {
      toast("Ошибка сохранения", "error");
    }
  };

  const set = <K extends keyof UISettings>(key: K, value: UISettings[K]) => {
    setSettings((s) => (s ? { ...s, [key]: value } : s));
  };

  if (loading || !settings) return <Spinner label="Загрузка настроек..." />;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="page-header">
        <h1>Настройки</h1>
        <p>Конфигурация агента и интеграций</p>
      </div>

      <div className="flex gap-1 border-b border-surface-border">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm transition-colors ${
              tab === t.id
                ? "border-b-2 border-accent font-medium text-accent"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="card space-y-4 p-4">
        {tab === "llm" && (
          <>
            <Field label="Provider" value={settings.llm_provider} onChange={(v) => set("llm_provider", v)} />
            <Field label="Model" value={settings.llm_model} onChange={(v) => set("llm_model", v)} />
            <Field label="API Key" value={settings.llm_api_key} onChange={(v) => set("llm_api_key", v)} type="password" />
            <Field label="Temperature" value={String(settings.temperature)} onChange={(v) => set("temperature", Number(v))} type="number" />
            <Field label="Max Tokens" value={String(settings.max_tokens)} onChange={(v) => set("max_tokens", Number(v))} type="number" />
          </>
        )}

        {tab === "search" && (
          <>
            <Field label="Период поиска (часов)" value={String(settings.search_interval_hours)} onChange={(v) => set("search_interval_hours", Number(v))} type="number" />
            <Field label="Мин. зарплата" value={String(settings.salary_min)} onChange={(v) => set("salary_min", Number(v))} type="number" />
            <Field label="Исключённые компании" value={settings.excluded_companies.join(", ")} onChange={(v) => set("excluded_companies", v.split(",").map((s) => s.trim()))} />
            <Field label="Ключевые слова" value={settings.keywords.join(", ")} onChange={(v) => set("keywords", v.split(",").map((s) => s.trim()))} />
            <Field label="Минус-слова" value={settings.minus_words.join(", ")} onChange={(v) => set("minus_words", v.split(",").map((s) => s.trim()))} />
            <Field label="Города" value={settings.cities.join(", ")} onChange={(v) => set("cities", v.split(",").map((s) => s.trim()))} />
            <Field label="Страны" value={settings.countries.join(", ")} onChange={(v) => set("countries", v.split(",").map((s) => s.trim()))} />
          </>
        )}

        {tab === "auto" && (
          <>
            <Toggle label="Автоматически откликаться" checked={settings.auto_apply} onChange={(v) => set("auto_apply", v)} />
            <Toggle label="Только после оценки AI" checked={settings.apply_after_ai_review} onChange={(v) => set("apply_after_ai_review", v)} />
            <Field label="Мин. % совпадения" value={String(settings.min_match_percent)} onChange={(v) => set("min_match_percent", Number(v))} type="number" />
            <Field label="Задержка между откликами (сек)" value={String(settings.apply_delay_seconds)} onChange={(v) => set("apply_delay_seconds", Number(v))} type="number" />
            <Field label="Макс. откликов в день" value={String(settings.max_applications_per_day)} onChange={(v) => set("max_applications_per_day", Number(v))} type="number" />
            <div className="grid grid-cols-2 gap-3">
              <Field label="Рабочие часы с" value={settings.work_hours_start} onChange={(v) => set("work_hours_start", v)} />
              <Field label="до" value={settings.work_hours_end} onChange={(v) => set("work_hours_end", v)} />
            </div>
          </>
        )}

        {tab === "telegram" && (
          <>
            <Field label="Bot Token" value={settings.telegram_token} onChange={(v) => set("telegram_token", v)} type="password" />
            <Field label="Chat ID" value={settings.telegram_chat_id} onChange={(v) => set("telegram_chat_id", v)} />
            <button className="btn-ghost border border-surface-border">Тест уведомления</button>
          </>
        )}

        {tab === "proxy" && (
          <>
            <Field label="Тип" value={settings.proxy_type} onChange={(v) => set("proxy_type", v)} />
            <Field label="Адрес" value={settings.proxy_host} onChange={(v) => set("proxy_host", v)} />
            <Field label="Логин" value={settings.proxy_login} onChange={(v) => set("proxy_login", v)} />
            <Field label="Пароль" value={settings.proxy_password} onChange={(v) => set("proxy_password", v)} type="password" />
          </>
        )}

        <button className="btn-primary" onClick={save}>Сохранить</button>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="block text-sm">
      <span className="text-[var(--text-muted)]">{label}</span>
      <input type={type} className="input mt-1" value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between text-sm">
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </label>
  );
}
