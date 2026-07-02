import { useCallback, useEffect, useRef, useState } from "react";
import { Check, FileUp, Loader2, Upload } from "lucide-react";
import { api } from "@/api/client";
import { CandidateProfileView } from "@/components/candidate/CandidateProfileView";
import { Mascot } from "@/components/ugra/Mascot";
import { Spinner } from "@/components/ui/Spinner";
import type { AnalysisStatus, CandidateProfile } from "@/types";

const ANALYSIS_STEP_LABELS: Record<string, string> = {
  extract_text: "Извлекаю текст",
  analyze_experience: "Анализирую опыт",
  determine_specialization: "Определяю специализацию",
  build_skills_map: "Строю карту навыков",
  analyze_career: "Анализирую карьерный путь",
  build_search_strategy: "Формирую поисковую стратегию",
  create_profile: "Создаю профиль кандидата",
  configure_ai: "Настраиваю AI",
};

export function ResumesPage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [profileWarning, setProfileWarning] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const pollErrorsRef = useRef(0);

  const loadProfile = useCallback(async () => {
    const data = await api.candidateProfile();
    setProfile(data.profile);
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadProfile();
    return () => clearInterval(pollRef.current);
  }, [loadProfile]);

  const pollAnalysis = (jobId: string) => {
    clearInterval(pollRef.current);
    pollErrorsRef.current = 0;

    const finish = async (status: AnalysisStatus) => {
      clearInterval(pollRef.current);
      setAnalyzing(false);
      if (status.error) setProfileWarning(status.error);
      if (status.profile) {
        setProfile(status.profile as CandidateProfile);
      } else {
        await loadProfile();
      }
    };

    const tick = async () => {
      try {
        const status = await api.analysisStatus(jobId);
        pollErrorsRef.current = 0;
        setAnalysisStatus(status);
        if (status.status === "completed") {
          await finish(status);
        } else if (status.status === "failed") {
          clearInterval(pollRef.current);
          setAnalyzing(false);
          setProfileWarning(null);
          setAnalysisStatus(status);
        }
      } catch {
        pollErrorsRef.current += 1;
        if (pollErrorsRef.current >= 8) {
          clearInterval(pollRef.current);
          setAnalyzing(false);
          setAnalysisStatus({
            job_id: jobId,
            status: "failed",
            current_step: "",
            steps_completed: [],
            progress: 0,
            error: "Не удалось получить статус анализа. Обновите страницу.",
            profile_ready: false,
          });
        }
      }
    };

    void tick();
    pollRef.current = setInterval(tick, 1200);
  };

  const handleUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Поддерживается только PDF");
      return;
    }
    setAnalyzing(true);
    setAnalysisStatus(null);
    setProfileWarning(null);
    try {
      const { job } = await api.uploadResumePdf(file);
      pollAnalysis(job.job_id);
    } catch (e) {
      setAnalyzing(false);
      alert(e instanceof Error ? e.message : "Ошибка загрузки");
    }
  };

  const triggerUpload = () => fileRef.current?.click();

  if (loading) return <Spinner label="Загрузка..." />;

  if (analyzing) {
    const steps = Object.keys(ANALYSIS_STEP_LABELS);
    const completedSteps = new Set(analysisStatus?.steps_completed ?? []);
    const progress = analysisStatus?.progress ?? 0;

    return (
      <div className="mx-auto max-w-xl space-y-8 py-12">
        <div className="flex flex-col items-center gap-4">
          <Mascot state="jobAnalysis" height={200} enableIdle={false} />
          <h1 className="text-xl font-semibold">Анализирую ваше резюме…</h1>
          <p className="text-center text-sm text-[var(--text-muted)]">
            После завершения вы автоматически перейдёте на экран профиля кандидата
          </p>
        </div>

        <div className="space-y-2">
          <div className="h-2 overflow-hidden rounded-full bg-surface-border">
            <div
              className="h-full rounded-full bg-accent transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-center text-sm text-[var(--text-muted)]">{progress}%</p>
        </div>

        <ul className="space-y-2">
          {steps.map((key) => {
            const done = completedSteps.has(key);
            const active = analysisStatus?.current_step === ANALYSIS_STEP_LABELS[key];
            return (
              <li
                key={key}
                className={`flex items-center gap-2 text-sm ${
                  done ? "text-success" : active ? "text-accent" : "text-[var(--text-muted)]"
                }`}
              >
                {done ? (
                  <Check className="h-4 w-4" />
                ) : active ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <span className="h-4 w-4" />
                )}
                {ANALYSIS_STEP_LABELS[key]}
              </li>
            );
          })}
        </ul>
      </div>
    );
  }

  if (analysisStatus?.status === "failed" && !profile) {
    return (
      <div className="mx-auto max-w-xl space-y-6 py-12 text-center">
        <h1 className="text-xl font-semibold text-danger">Анализ не завершён</h1>
        <p className="text-sm text-subtitle">{analysisStatus.error}</p>
        <button type="button" className="btn-primary" onClick={triggerUpload}>
          <Upload className="h-4 w-4" />
          Попробовать снова
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && void handleUpload(e.target.files[0])}
        />
      </div>
    );
  }

  if (profile) {
    return (
      <>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && void handleUpload(e.target.files[0])}
        />
        {profileWarning && (
          <div className="mb-4 rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-[var(--text)]">
            {profileWarning}
          </div>
        )}
        <CandidateProfileView
          profile={profile}
          onProfileUpdate={setProfile}
          onReupload={triggerUpload}
          onRescan={triggerUpload}
        />
      </>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="page-header">
          <h1>Профиль кандидата</h1>
          <p>Загрузите PDF — Ugra построит внутренний профиль и начнёт искать вакансии</p>
        </div>
        <button type="button" className="btn-primary" onClick={triggerUpload}>
          <Upload className="h-4 w-4" />
          Загрузить PDF
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && void handleUpload(e.target.files[0])}
        />
      </div>

      <div
        className="card flex cursor-pointer flex-col items-center justify-center gap-3 border-dashed py-16"
        onClick={triggerUpload}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const f = e.dataTransfer.files[0];
          if (f) void handleUpload(f);
        }}
      >
        <FileUp className="h-10 w-10 text-[var(--text-muted)]" />
        <p className="text-sm text-[var(--text-muted)]">
          Перетащите PDF сюда или нажмите «Загрузить PDF»
        </p>
      </div>
    </div>
  );
}
