import type {
  AnalysisStatus,
  Application,
  CandidateProfile,
  EmployerPreview,
  ProfileHistoryEntry,
  CoverLetterTemplate,
  DashboardStats,
  Job,
  LogEntry,
  Resume,
  SourceInfo,
  SystemStatus,
  TimelineEntry,
  UISettings,
} from "@/types";

const API = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  dashboard: () =>
    request<{ stats: DashboardStats; timeline: TimelineEntry[] }>("/ui/dashboard"),

  searchJobs: (params: Record<string, string | number | boolean | string[]>) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (Array.isArray(v)) v.forEach((item) => q.append(k, item));
      else if (v !== "" && v !== undefined) q.set(k, String(v));
    });
    return request<{ jobs: Job[]; count: number }>(`/ui/jobs/search?${q}`, { method: "POST" });
  },

  apply: (job: Job, resume_title = "", cover_letter = "") =>
    request<{ application: Application }>("/ui/applications/apply", {
      method: "POST",
      body: JSON.stringify({ job, resume_title, cover_letter }),
    }),

  ignoreJob: (jobId: string) =>
    request<{ ok: boolean }>(`/ui/jobs/${jobId}/ignore`, { method: "POST" }),

  applications: () => request<{ applications: Application[] }>("/ui/applications"),

  application: (id: string) => request<Application>(`/ui/applications/${id}`),

  resumes: () => request<{ resumes: Resume[] }>("/ui/resumes"),

  uploadResumePdf: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/ui/resumes/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<{ job: { job_id: string; status: string; progress: number } }>;
  },

  analysisStatus: (jobId: string) =>
    request<AnalysisStatus>(`/ui/resumes/analysis/${jobId}`),

  candidateProfile: () =>
    request<{ profile: CandidateProfile | null }>("/ui/candidate-profile"),

  updateCandidateProfile: (data: Partial<{
    primary_specialization: string;
    level: string;
    preferred_roles: { title: string; priority: string }[];
    include_keywords: string[];
    exclude_keywords: string[];
    excluded_roles: string[];
  }>) =>
    request<{ profile: CandidateProfile }>("/ui/candidate-profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  profileHistory: () =>
    request<{ history: ProfileHistoryEntry[] }>("/ui/candidate-profile/history"),

  employerPreview: () =>
    request<EmployerPreview>("/ui/candidate-profile/employer-preview"),

  saveResume: (data: Partial<Resume> & { title: string }) =>
    request<Resume>("/ui/resumes", { method: "POST", body: JSON.stringify(data) }),

  deleteResume: (id: string) =>
    request<{ ok: boolean }>(`/ui/resumes/${id}`, { method: "DELETE" }),

  coverLetters: () => request<{ templates: CoverLetterTemplate[] }>("/ui/cover-letters"),

  saveCoverLetter: (data: Partial<CoverLetterTemplate> & { title: string }) =>
    request<CoverLetterTemplate>("/ui/cover-letters", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteCoverLetter: (id: string) =>
    request<{ ok: boolean }>(`/ui/cover-letters/${id}`, { method: "DELETE" }),

  sources: () => request<{ sources: SourceInfo[] }>("/ui/sources"),

  settings: () => request<UISettings>("/ui/settings"),

  updateSettings: (data: Partial<UISettings>) =>
    request<UISettings>("/ui/settings", { method: "PATCH", body: JSON.stringify(data) }),

  logs: (level?: string, search?: string) => {
    const q = new URLSearchParams();
    if (level) q.set("level", level);
    if (search) q.set("search", search);
    return request<{ logs: LogEntry[] }>(`/ui/logs?${q}`);
  },

  status: () => request<SystemStatus>("/ui/status"),

  generateCoverLetterTemplate: (data: {
    template_id?: string;
    job_title?: string;
    company?: string;
    job_description?: string;
  }) =>
    request<{ cover_letter: string; warning?: string | null }>("/ui/cover-letters/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateCoverLetter: (job: Job, resumes: Resume[]) =>
    request<{ cover_letter: string }>(`/jobs/${job.id}/cover-letter`, {
      method: "POST",
      body: JSON.stringify({ job, resumes: resumes.map((r) => ({ title: r.title, content: r.content })) }),
    }),
};

export function subscribeTimeline(
  onUpdate: (data: { timeline: TimelineEntry[]; stats?: DashboardStats }) => void,
) {
  const source = new EventSource(`${API}/ui/timeline/stream`);
  source.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onUpdate(data);
    } catch {
      /* ignore */
    }
  };
  return () => source.close();
}
