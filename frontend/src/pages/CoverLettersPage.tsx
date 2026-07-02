import { useEffect, useState } from "react";
import { Loader2, Plus, Sparkles, Trash2 } from "lucide-react";
import { api } from "@/api/client";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/stores/toast";
import type { CoverLetterTemplate } from "@/types";
import { formatDate } from "@/lib/utils";

export function CoverLettersPage() {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<CoverLetterTemplate[]>([]);
  const [selected, setSelected] = useState<CoverLetterTemplate | null>(null);
  const [editing, setEditing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [form, setForm] = useState({ title: "", content: "", suitable_for: "" });
  const [genForm, setGenForm] = useState({ job_title: "", company: "", job_description: "" });
  const [showGenForm, setShowGenForm] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = () => api.coverLetters().then((d) => setTemplates(d.templates));

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, []);

  const save = async () => {
    if (!form.title.trim()) {
      toast("Укажите название шаблона", "error");
      return;
    }
    try {
      const saved = await api.saveCoverLetter({
        id: selected?.id,
        title: form.title,
        content: form.content,
        suitable_for: form.suitable_for.split(",").map((s) => s.trim()).filter(Boolean),
      });
      await load();
      setSelected(saved);
      setEditing(false);
      toast("Шаблон сохранён", "success");
    } catch {
      toast("Ошибка сохранения", "error");
    }
  };

  const remove = async (id: string) => {
    await api.deleteCoverLetter(id);
    await load();
    if (selected?.id === id) setSelected(null);
    toast("Шаблон удалён", "info");
  };

  const generateAi = async () => {
    if (!selected) return;
    setGenerating(true);
    try {
      const { cover_letter, warning } = await api.generateCoverLetterTemplate({
        template_id: selected.id,
        job_title: genForm.job_title || selected.suitable_for[0] || selected.title,
        company: genForm.company || "Компания",
        job_description: genForm.job_description,
      });
      await load();
      const updated = (await api.coverLetters()).templates.find((t) => t.id === selected.id);
      if (updated) setSelected(updated);
      setForm({
        title: selected.title,
        content: cover_letter,
        suitable_for: selected.suitable_for.join(", "),
      });
      setEditing(true);
      setShowGenForm(false);
      toast(
        warning ?? "Письмо сгенерировано и сохранено в шаблон",
        warning ? "info" : "success",
      );
    } catch (e) {
      toast(e instanceof Error ? e.message : "Ошибка генерации", "error");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <Spinner label="Загрузка шаблонов..." />;

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="page-header">
        <h1>Сопроводительные письма</h1>
        <p>Шаблоны сохраняются на диск и не пропадают после перезапуска</p>
      </div>

      <div className="flex min-h-0 flex-1 gap-4">
        <div className="card w-72 shrink-0 overflow-auto">
          <div className="flex items-center justify-between border-b border-surface-border p-3">
            <h2 className="text-sm font-medium">Шаблоны</h2>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => {
                setForm({ title: "", content: "", suitable_for: "" });
                setSelected(null);
                setEditing(true);
              }}
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
          <ul>
            {templates.length === 0 ? (
              <li className="p-3 text-sm text-subtitle">Нет шаблонов</li>
            ) : (
              templates.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelected(t);
                      setEditing(false);
                      setShowGenForm(false);
                      setGenForm({
                        job_title: t.suitable_for[0] || t.title,
                        company: "",
                        job_description: "",
                      });
                    }}
                    className={`w-full px-3 py-2 text-left text-sm hover:bg-accent-light-hover ${selected?.id === t.id ? "bg-accent-light text-accent-text" : ""}`}
                  >
                    {t.title}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="card min-w-0 flex-1 overflow-auto p-4">
          {editing ? (
            <div className="mx-auto max-w-2xl space-y-3">
              <h2 className="text-lg font-semibold">{selected ? "Редактировать" : "Новый шаблон"}</h2>
              <input
                className="input"
                placeholder="Название"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              />
              <input
                className="input"
                placeholder="Подходит для (через запятую)"
                value={form.suitable_for}
                onChange={(e) => setForm((f) => ({ ...f, suitable_for: e.target.value }))}
              />
              <textarea
                className="input min-h-64 font-mono text-sm"
                value={form.content}
                onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
              />
              <div className="flex gap-2">
                <button type="button" className="btn-primary" onClick={() => void save()}>
                  Сохранить
                </button>
                <button type="button" className="btn-ghost" onClick={() => setEditing(false)}>
                  Отмена
                </button>
              </div>
            </div>
          ) : selected ? (
            <>
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{selected.title}</h2>
                  <p className="text-sm text-subtitle">
                    Изменён {formatDate(selected.updated_at)} · использован {selected.usage_count} раз
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => {
                      setForm({
                        title: selected.title,
                        content: selected.content,
                        suitable_for: selected.suitable_for.join(", "),
                      });
                      setEditing(true);
                    }}
                  >
                    Редактировать
                  </button>
                  <button
                    type="button"
                    className="btn-ghost text-danger"
                    onClick={() => void remove(selected.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="mt-4">
                <div className="text-xs text-subtitle">Подходит для</div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {selected.suitable_for.map((s) => (
                    <span key={s} className="rounded bg-surface-border px-2 py-0.5 text-xs">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <pre className="mt-4 whitespace-pre-wrap rounded-xl border border-surface-border bg-surface-elevated p-4 text-sm">
                {selected.content}
              </pre>

              {showGenForm && (
                <div className="mt-4 space-y-3 rounded-xl border border-accent/20 bg-accent-light/40 p-4">
                  <h3 className="text-sm font-medium">Параметры для AI</h3>
                  <input
                    className="input"
                    placeholder="Должность"
                    value={genForm.job_title}
                    onChange={(e) => setGenForm((f) => ({ ...f, job_title: e.target.value }))}
                  />
                  <input
                    className="input"
                    placeholder="Компания"
                    value={genForm.company}
                    onChange={(e) => setGenForm((f) => ({ ...f, company: e.target.value }))}
                  />
                  <textarea
                    className="input min-h-24"
                    placeholder="Описание вакансии (опционально)"
                    value={genForm.job_description}
                    onChange={(e) => setGenForm((f) => ({ ...f, job_description: e.target.value }))}
                  />
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  className="btn-primary"
                  disabled={generating}
                  onClick={() => {
                    if (!showGenForm) {
                      setShowGenForm(true);
                      return;
                    }
                    void generateAi();
                  }}
                >
                  {generating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  {generating ? "Генерация…" : showGenForm ? "Сгенерировать AI" : "Сгенерировать AI"}
                </button>
                {showGenForm && (
                  <button type="button" className="btn-ghost" onClick={() => setShowGenForm(false)}>
                    Отмена
                  </button>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-subtitle">Выберите шаблон или создайте новый</p>
          )}
        </div>
      </div>
    </div>
  );
}
