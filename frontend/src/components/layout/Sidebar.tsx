import { NavLink } from "react-router-dom";
import {
  FileText,
  LayoutDashboard,
  Mail,
  Moon,
  ScrollText,
  Search,
  Send,
  Settings,
  Sun,
  Zap,
} from "lucide-react";
import { useTheme } from "@/stores/theme";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/jobs", icon: Search, label: "Поиск вакансий" },
  { to: "/applications", icon: Send, label: "Отклики" },
  { to: "/cover-letters", icon: Mail, label: "Сопроводительные" },
  { to: "/resumes", icon: FileText, label: "Профиль кандидата" },
  { to: "/sources", icon: Zap, label: "Источники" },
  { to: "/settings", icon: Settings, label: "Настройки" },
  { to: "/logs", icon: ScrollText, label: "Логи" },
];

export function Sidebar() {
  const { theme, toggle } = useTheme();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-surface-border bg-[var(--sidebar)]">
      <div className="flex items-center gap-3 border-b border-surface-border px-4 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-sm font-bold text-white shadow-sm">
          U
        </div>
        <div>
          <div className="text-sm font-semibold">Ugra</div>
          <div className="text-xs text-subtitle">Career Agent</div>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 p-2">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-accent-light font-medium text-accent-text"
                  : "text-[var(--text-muted)] hover:bg-accent-light-hover hover:text-[var(--text)]",
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={cn("h-4 w-4", isActive ? "text-accent" : "")} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-surface-border p-2">
        <button type="button" onClick={toggle} className="btn-ghost w-full justify-start">
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {theme === "dark" ? "Светлая тема" : "Тёмная тема"}
        </button>
      </div>
    </aside>
  );
}
