import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ApplicationsPage } from "@/pages/ApplicationsPage";
import { CoverLettersPage } from "@/pages/CoverLettersPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { JobsPage } from "@/pages/JobsPage";
import { LogsPage } from "@/pages/LogsPage";
import { ResumesPage } from "@/pages/ResumesPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { SourcesPage } from "@/pages/SourcesPage";
import { ThemeProvider } from "@/stores/theme";
import { ToastProvider } from "@/stores/toast";

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="jobs" element={<JobsPage />} />
              <Route path="applications" element={<ApplicationsPage />} />
              <Route path="cover-letters" element={<CoverLettersPage />} />
              <Route path="resumes" element={<ResumesPage />} />
              <Route path="sources" element={<SourcesPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="logs" element={<LogsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}
