import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMyTeams, fetchMyProjects } from "../api/me";
import { createTeam } from "../api/teams";
import { createProject } from "../api/projects";
import { useLanguage } from "../i18n/LanguageContext";
import { useAuth } from "../context/AuthContext";
import type { MyProjectOut, MyTeamOut } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { TeamStatusBar } from "../components/TeamStatusBar";

const INTRO_DISMISSED_KEY = "neomeo_dashboard_intro_dismissed";

function greetingKey(hour: number): string {
  if (hour >= 5 && hour < 12) return "dashboard.greetingMorning";
  if (hour >= 12 && hour < 18) return "dashboard.greetingAfternoon";
  if (hour >= 18 && hour < 23) return "dashboard.greetingEvening";
  return "dashboard.greetingNight";
}

export function DashboardPage() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [teams, setTeams] = useState<MyTeamOut[] | null>(null);
  const [projects, setProjects] = useState<MyProjectOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showIntro, setShowIntro] = useState(() => localStorage.getItem(INTRO_DISMISSED_KEY) !== "1");
  const displayName = user?.name ?? user?.github_handle ?? null;

  function dismissIntro() {
    localStorage.setItem(INTRO_DISMISSED_KEY, "1");
    setShowIntro(false);
  }

  const [showTeamForm, setShowTeamForm] = useState(false);
  const [teamName, setTeamName] = useState("");
  const [teamTimezone, setTeamTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const [teamCountry, setTeamCountry] = useState("");
  const [teamLanguage, setTeamLanguage] = useState<"ko" | "en">("ko");

  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [projectTeamId, setProjectTeamId] = useState("");

  function reload() {
    fetchMyTeams().then(setTeams).catch((err) => setError(errorMessage(err)));
    fetchMyProjects().then(setProjects).catch((err) => setError(errorMessage(err)));
  }

  useEffect(reload, []);

  async function handleCreateTeam(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createTeam({
        name: teamName,
        timezone: teamTimezone,
        country: teamCountry || undefined,
        default_language: teamLanguage,
      });
      setTeamName("");
      setShowTeamForm(false);
      reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createProject({ name: projectName, team_id: projectTeamId });
      setProjectName("");
      setShowProjectForm(false);
      reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div className="page">
      <div className="dashboard-hero">
        <div className="landing-eyebrow">
          <span className="landing-eyebrow-dot" />
          {t("dashboard.eyebrow")}
        </div>
        <h1>
          {t(greetingKey(new Date().getHours()))}
          {displayName ? `, ${displayName}` : ""}
        </h1>
      </div>

      {teams && teams.length > 0 && (
        <div className="dashboard-hero" style={{ marginBottom: 8 }}>
          <h2 style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-dim)" }}>
            {t("dashboard.teamStatus")}
          </h2>
          <TeamStatusBar teams={teams} />
        </div>
      )}

      {showIntro && (
        <div className="intro-banner">
          <span className="intro-banner-icon">i</span>
          <div className="intro-banner-body">
            <strong>{t("dashboard.introTitle")}</strong>
            <p>
              {t("dashboard.introIntro")}
              <strong> {t("dashboard.introTimeline")}</strong>
              {t("dashboard.introTimelineParen")}
              <strong>{t("dashboard.introBriefing")}</strong>
              {t("dashboard.introBriefingParen")}
              <strong>{t("dashboard.introSettings")}</strong>
              {t("dashboard.introSettingsParen")}
            </p>
          </div>
          <button className="intro-banner-close" onClick={dismissIntro} aria-label={t("dashboard.introClose")}>
            ×
          </button>
        </div>
      )}

      <ErrorBanner message={error} />

      <section>
        <div className="row">
          <h2>{t("dashboard.myTeams")}</h2>
          <button onClick={() => setShowTeamForm((v) => !v)}>
            {showTeamForm ? t("common.cancel") : t("dashboard.newTeam")}
          </button>
        </div>

        {showTeamForm && (
          <form onSubmit={handleCreateTeam} className="card stack">
            <div className="field">
              <label>{t("dashboard.teamNameLabel")}</label>
              <input value={teamName} onChange={(e) => setTeamName(e.target.value)} required />
            </div>
            <div className="field">
              <label>{t("dashboard.timezoneLabel")}</label>
              <input value={teamTimezone} onChange={(e) => setTeamTimezone(e.target.value)} required />
            </div>
            <div className="field">
              <label>{t("dashboard.countryLabel")}</label>
              <input value={teamCountry} onChange={(e) => setTeamCountry(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("dashboard.defaultLanguageLabel")}</label>
              <select value={teamLanguage} onChange={(e) => setTeamLanguage(e.target.value as "ko" | "en")}>
                <option value="ko">{t("common.korean")}</option>
                <option value="en">{t("common.english")}</option>
              </select>
            </div>
            <button type="submit" className="primary">
              {t("common.create")}
            </button>
          </form>
        )}

        {teams === null ? (
          <div className="spinner">{t("common.loading")}</div>
        ) : teams.length === 0 ? (
          <div className="empty-state">{t("dashboard.noTeams")}</div>
        ) : (
          <div className="entity-grid">
            {teams.map((t2) => (
              <Link key={t2.id} to={`/teams/${t2.id}`} className="entity-card">
                <span className="entity-card-icon">{t2.name.slice(0, 1)}</span>
                <span className="entity-card-name">{t2.name}</span>
                <span className="entity-card-sub">
                  {t2.timezone} · {t2.work_start}–{t2.work_end}
                </span>
                <span className="entity-card-footer">
                  <span className={`badge ${t2.role === "leader" ? "accent" : "muted"}`}>
                    {t2.role === "leader" ? t("common.leader") : t("common.member")}
                  </span>
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: 32 }}>
        <div className="row">
          <h2>{t("dashboard.myProjects")}</h2>
          <button onClick={() => setShowProjectForm((v) => !v)}>
            {showProjectForm ? t("common.cancel") : t("dashboard.newProject")}
          </button>
        </div>

        {showProjectForm && (
          <form onSubmit={handleCreateProject} className="card stack">
            <div className="field">
              <label>{t("dashboard.projectNameLabel")}</label>
              <input value={projectName} onChange={(e) => setProjectName(e.target.value)} required />
            </div>
            <div className="field">
              <label>{t("dashboard.teamSelectLabel")}</label>
              <select value={projectTeamId} onChange={(e) => setProjectTeamId(e.target.value)} required>
                <option value="" disabled>
                  {t("dashboard.teamSelectPlaceholder")}
                </option>
                {teams?.map((t2) => (
                  <option key={t2.id} value={t2.id}>
                    {t2.name}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="primary">
              {t("common.create")}
            </button>
          </form>
        )}

        {projects === null ? (
          <div className="spinner">{t("common.loading")}</div>
        ) : projects.length === 0 ? (
          <div className="empty-state">{t("dashboard.noProjects")}</div>
        ) : (
          <div className="entity-grid">
            {projects.map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`} className="entity-card">
                <span className="entity-card-icon">{p.name.slice(0, 1)}</span>
                <span className="entity-card-name">{p.name}</span>
                {p.repo_full_name && <span className="entity-card-sub">{p.repo_full_name}</span>}
                <span className="entity-card-footer">
                  {p.repo_full_name ? (
                    <span className="badge ok">{t("dashboard.githubConnected")}</span>
                  ) : (
                    <span className="badge muted">{t("dashboard.githubNotConnected")}</span>
                  )}
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
