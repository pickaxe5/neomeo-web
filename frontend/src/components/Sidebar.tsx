import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { fetchMyTeams, fetchMyProjects } from "../api/me";
import type { MyProjectOut, MyTeamOut } from "../types/api";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Sidebar() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const displayName = user?.name ?? user?.github_handle ?? user?.email ?? t("common.user");
  const [teams, setTeams] = useState<MyTeamOut[] | null>(null);
  const [projects, setProjects] = useState<MyProjectOut[] | null>(null);

  useEffect(() => {
    fetchMyTeams().then(setTeams).catch(() => setTeams([]));
    fetchMyProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-ko">너머</span>
        <span className="sidebar-brand-en">NEOMEO</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M2 8.5 8 3l6 5.5M4 7v6h8V7"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {t("common.dashboard")}
        </NavLink>

        {teams && teams.length > 0 && (
          <>
            <div className="sidebar-nav-label">{t("dashboard.myTeams")}</div>
            {teams.map((team) => (
              <NavLink key={team.id} to={`/teams/${team.id}`} className={({ isActive }) => (isActive ? "active" : "")}>
                <span className="sidebar-nav-dot" />
                {team.name}
              </NavLink>
            ))}
          </>
        )}

        {projects && projects.length > 0 && (
          <>
            <div className="sidebar-nav-label">{t("dashboard.myProjects")}</div>
            {projects.map((project) => (
              <NavLink
                key={project.id}
                to={`/projects/${project.id}`}
                className={({ isActive }) => (isActive ? "active" : "")}
              >
                <span className="sidebar-nav-dot accent" />
                {project.name}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="sidebar-footer">
        <LanguageSwitcher className="sidebar-lang" />
        <div className="sidebar-user">
          <span className="avatar">{displayName.slice(0, 1)}</span>
          <span className="sidebar-user-name">{displayName}</span>
        </div>
        <button onClick={logout}>{t("common.logout")}</button>
      </div>
    </aside>
  );
}
