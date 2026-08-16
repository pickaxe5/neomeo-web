import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { Sidebar } from "./Sidebar";

export function AppShell() {
  const { isAuthenticated, loading } = useAuth();
  const { t } = useLanguage();

  if (loading) {
    return <div className="spinner">{t("common.loading")}</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
