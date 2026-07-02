import { cn } from "@/lib/utils";

const variants: Record<string, string> = {
  sent: "bg-blue-500/15 text-blue-400",
  viewed: "bg-purple-500/15 text-purple-400",
  response: "bg-success/15 text-green-400",
  replied: "bg-success/15 text-green-400",
  rejected: "bg-danger/15 text-red-400",
  invite: "bg-amber-500/15 text-amber-400",
  invitation: "bg-amber-500/15 text-amber-400",
  error: "bg-danger/15 text-red-400",
  new: "bg-surface-border text-[var(--text-muted)]",
  analyzed: "bg-accent/15 text-blue-400",
  applied: "bg-blue-500/15 text-blue-400",
};

const labels: Record<string, string> = {
  sent: "Отправлен",
  viewed: "Просмотрен",
  response: "Есть ответ",
  replied: "Есть ответ",
  rejected: "Отказ",
  invite: "Приглашение",
  invitation: "Приглашение",
  error: "Ошибка",
  new: "Новый",
  analyzed: "Проанализирован",
  applied: "Отправлен",
};

export function StatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        variants[key] ?? "bg-surface-border text-[var(--text-muted)]",
      )}
    >
      {labels[key] ?? status}
    </span>
  );
}
