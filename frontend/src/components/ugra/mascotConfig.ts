/** Agent states for the Ugra mascot — maps to PNG poses and UI copy. */

export type AgentState =
  | "idle"
  | "searching"
  | "jobAnalysis"
  | "fitAssessment"
  | "preparingApplication"
  | "sendingApplication"
  | "waiting"
  | "responseReceived"
  | "invitation"
  | "rejection"
  | "error"
  | "noJobs"
  | "success"
  | "planning"
  | "statistics"
  | "saveVacancy"
  | "night";

export interface MascotStateConfig {
  pose: string;
  status: string;
  messages: string[];
  progress?: boolean;
}

export const MASCOT_STATES: Record<AgentState, MascotStateConfig> = {
  idle: {
    pose: "states/greeting",
    status: "На связи",
    messages: ["Привет! Я готова помочь с поиском работы.", "Слежу за новыми вакансиями."],
  },
  searching: {
    pose: "states/job-search",
    status: "Ищу вакансии",
    messages: ["Просматриваю новые вакансии…", "Сканирую площадки на подходящие предложения."],
    progress: true,
  },
  jobAnalysis: {
    pose: "states/job-analysis",
    status: "Анализирую",
    messages: ["Сравниваю требования с вашим резюме…", "Изучаю описание вакансии и стек технологий."],
    progress: true,
  },
  fitAssessment: {
    pose: "states/fit-assessment",
    status: "Оцениваю соответствие",
    messages: ["Считаю Match Score…", "Определяю плюсы, минусы и skill gaps."],
    progress: true,
  },
  preparingApplication: {
    pose: "states/prepare-response",
    status: "Готовлю отклик",
    messages: ["Готовлю персонализированный отклик…", "Подбираю резюме и сопроводительное письмо."],
    progress: true,
  },
  sendingApplication: {
    pose: "states/send-response",
    status: "Отправляю отклик",
    messages: ["Отправляю отклик работодателю…", "Почти готово — письмо уходит!"],
    progress: true,
  },
  waiting: {
    pose: "states/waiting",
    status: "Ожидаю ответа",
    messages: ["Жду ответа работодателя.", "Отклик отправлен — ждём обратной связи."],
  },
  responseReceived: {
    pose: "states/response-received",
    status: "Получен ответ",
    messages: ["Работодатель ответил на отклик!", "Есть новости по вашей заявке."],
  },
  invitation: {
    pose: "states/invitation",
    status: "Приглашение!",
    messages: ["Отличные новости! Вас пригласили на интервью 🎉", "Поздравляю — приглашение на собеседование!"],
  },
  rejection: {
    pose: "states/rejection",
    status: "Отказ",
    messages: ["К сожалению, отказ по этой вакансии.", "Не расстраивайтесь — найдём лучший вариант."],
  },
  error: {
    pose: "states/error",
    status: "Ошибка",
    messages: ["Что-то пошло не так. Попробую снова.", "Возникла ошибка — уже разбираюсь."],
  },
  noJobs: {
    pose: "states/no-jobs",
    status: "Нет подходящих",
    messages: ["Пока подходящих вакансий нет. Проверю снова позже.", "Ничего подходящего не нашла — продолжу мониторинг."],
  },
  success: {
    pose: "states/success",
    status: "Успех!",
    messages: ["Отличный результат! Продолжаем в том же духе.", "Получено предложение — это победа!"],
  },
  planning: {
    pose: "states/planning",
    status: "Планирую",
    messages: ["Составляю план действий на сегодня.", "Приоритизирую вакансии и отклики."],
  },
  statistics: {
    pose: "states/statistics",
    status: "Анализирую статистику",
    messages: ["Смотрю на результаты поиска.", "Обновляю сводку по вакансиям и откликам."],
  },
  saveVacancy: {
    pose: "states/save-vacancy",
    status: "Сохраняю вакансию",
    messages: ["Добавляю интересную вакансию в избранное.", "Запомнила эту позицию для вас."],
  },
  night: {
    pose: "states/night-work",
    status: "Ночная смена",
    messages: ["Продолжаю мониторинг в фоновом режиме.", "Работаю, пока вы отдыхаете."],
  },
};

/** Calm poses cycled during idle animation */
export const IDLE_CYCLE_POSES = [
  "states/greeting",
  "states/planning",
  "states/statistics",
] as const;

export const IDLE_DELAY_MS = 20_000;
export const IDLE_CYCLE_MS = 4_000;
export const MASCOT_FADE_MS = 300;

/** Map timeline event_type or source label → AgentState */
const EVENT_STATE_MAP: Record<string, AgentState> = {
  VacancyFound: "searching",
  JobAnalyzed: "fitAssessment",
  SkillGapDetected: "jobAnalysis",
  ApplicationSubmitted: "sendingApplication",
  InterviewReceived: "invitation",
  InterviewScheduled: "invitation",
  OfferReceived: "success",
  AgentStateChanged: "statistics",
  NotificationSent: "responseReceived",
  ResumeUpdated: "saveVacancy",
  LearningCompleted: "planning",
  GoalProgressUpdated: "planning",
  search: "searching",
  error: "error",
  idle: "idle",
  thinking: "jobAnalysis",
  working: "sendingApplication",
  rejection: "rejection",
  waiting: "waiting",
  no_jobs: "noJobs",
  night: "night",
};

/** Fallback from Russian timeline titles */
const TITLE_STATE_MAP: [string, AgentState][] = [
  ["Найдена новая вакансия", "searching"],
  ["Оценка соответствия", "fitAssessment"],
  ["Отправлен отклик", "sendingApplication"],
  ["Приглашение", "invitation"],
  ["skill gap", "jobAnalysis"],
  ["Обнаружен skill gap", "jobAnalysis"],
  ["Поиск завершён", "statistics"],
  ["Прогресс цели", "planning"],
  ["Резюме обновлено", "saveVacancy"],
  ["Состояние:", "statistics"],
  ["Ошибка", "error"],
  ["проигнорирована", "planning"],
];

export function resolveAgentState(eventType: string, title = "", detail = ""): AgentState {
  if (eventType && EVENT_STATE_MAP[eventType]) {
    return EVENT_STATE_MAP[eventType];
  }
  const haystack = `${title} ${detail}`.toLowerCase();
  for (const [needle, state] of TITLE_STATE_MAP) {
    if (haystack.includes(needle.toLowerCase())) return state;
  }
  if (eventType) return "idle";
  return "idle";
}

export function pickMessage(state: AgentState, detail?: string): string {
  const config = MASCOT_STATES[state];
  if (detail && detail.length > 3 && detail.length < 120) {
    return detail;
  }
  const idx = Math.floor(Date.now() / 30_000) % config.messages.length;
  return config.messages[idx];
}
