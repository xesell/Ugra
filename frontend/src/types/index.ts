export interface DashboardStats {
  found: number;
  suitable: number;
  applied: number;
  responses: number;
  invites: number;
  errors: number;
}

export interface TimelineEntry {
  id: string;
  time: string;
  source: string;
  title: string;
  detail: string;
  event_type: string;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  url: string;
  source: string;
  match_score: number;
  match_percentage: string;
  pros: string[];
  cons: string[];
  skill_gaps: string[];
  technologies: string[];
  description?: string;
  salary_from?: number;
  salary_to?: number;
  is_remote?: boolean;
  recommended?: boolean;
}

export interface Application {
  id: string;
  job_id: string;
  company: string;
  title: string;
  url: string;
  source: string;
  status: string;
  sent_at: string;
  updated_at: string;
  resume_title: string;
  cover_letter_preview: string;
  history: { time: string; action: string }[];
  employer_reply: string;
}

export interface Resume {
  id: string;
  title: string;
  skills: string[];
  experience_years: number;
  content: string;
  is_default: boolean;
  version: number;
  updated_at: string;
}

export interface CoverLetterTemplate {
  id: string;
  title: string;
  content: string;
  updated_at: string;
  suitable_for: string[];
  usage_count: number;
}

export interface TechSkill {
  name: string;
  category: string;
  confidence: number;
}

export interface CandidateProfile {
  user_id: string;
  identity: {
    full_name: string;
    primary_specialization: string;
    secondary_specializations: string[];
    level: string;
    level_rationale: string;
  };
  experience: {
    total_years: number;
    commercial_years: number;
    leadership_years: number;
    architecture_years: number;
    ai_years: number;
    devops_years: number;
    backend_years: number;
    frontend_years: number;
    analytics_years: number;
  };
  skills: TechSkill[];
  domains: string[];
  strengths: string[];
  weaknesses: string[];
  preferred_roles: { title: string; priority: string }[];
  search_strategy: {
    include_keywords: string[];
    exclude_keywords: string[];
    preferred_roles: string[];
    excluded_roles: string[];
  };
  prompt_context: string;
  ai_summary: string[];
  analysis_meta: {
    model: string;
    provider: string;
    duration_seconds: number;
    resume_filename: string;
  };
  analysis_stats: {
    skills_count: number;
    technologies_count: number;
    companies_count: number;
    projects_count: number;
    domains_count: number;
    roles_count: number;
  };
  version: number;
  analyzed_at: string;
}

export interface ProfileHistoryEntry {
  version: number;
  analyzed_at: string;
  model: string;
  duration_seconds: number;
  changes_summary: string;
  trigger: string;
}

export interface EmployerPreview {
  resume_filename: string;
  resume_excerpt: string;
  cover_letter: string;
  match_rationale: string[];
}

export interface AnalysisStatus {
  job_id: string;
  status: string;
  current_step: string;
  steps_completed: string[];
  progress: number;
  error: string;
  profile_ready: boolean;
  profile?: CandidateProfile;
}

export interface SourceInfo {
  id: string;
  name: string;
  connected: boolean;
  last_sync: string | null;
  token_expires: string | null;
  vacancies_found: number;
}

export interface LogEntry {
  id: string;
  time: string;
  level: string;
  service: string;
  message: string;
}

export interface SystemStatus {
  llm: { provider: string; model: string };
  sources: { hh: string; geekjob: string };
  telegram: string;
  cpu_percent: number;
  ram_gb: number;
  last_sync: string;
  agent_mood: string;
  active_agent: string | null;
}

export interface UISettings {
  llm_provider: string;
  llm_model: string;
  llm_api_key: string;
  temperature: number;
  max_tokens: number;
  search_interval_hours: number;
  salary_min: number;
  excluded_companies: string[];
  keywords: string[];
  minus_words: string[];
  cities: string[];
  countries: string[];
  auto_apply: boolean;
  apply_after_ai_review: boolean;
  min_match_percent: number;
  apply_delay_seconds: number;
  max_applications_per_day: number;
  work_hours_start: string;
  work_hours_end: string;
  telegram_token: string;
  telegram_chat_id: string;
  proxy_type: string;
  proxy_host: string;
  proxy_login: string;
  proxy_password: string;
}
