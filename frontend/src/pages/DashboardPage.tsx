import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMyTeams, fetchMyProjects } from "../api/me";
import { createTeam } from "../api/teams";
import { createProject } from "../api/projects";
import type { MyProjectOut, MyTeamOut } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function DashboardPage() {
  const [teams, setTeams] = useState<MyTeamOut[] | null>(null);
  const [projects, setProjects] = useState<MyProjectOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      <h1>대시보드</h1>
      <ErrorBanner message={error} />

      <section>
        <div className="row">
          <h2>내 프로젝트</h2>
          <button onClick={() => setShowProjectForm((v) => !v)}>
            {showProjectForm ? "취소" : "+ 새 프로젝트"}
          </button>
        </div>

        {showProjectForm && (
          <form onSubmit={handleCreateProject} className="card stack">
            <div className="field">
              <label>프로젝트 이름</label>
              <input value={projectName} onChange={(e) => setProjectName(e.target.value)} required />
            </div>
            <div className="field">
              <label>소속 팀</label>
              <select value={projectTeamId} onChange={(e) => setProjectTeamId(e.target.value)} required>
                <option value="" disabled>
                  팀을 선택하세요
                </option>
                {teams?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="primary">
              생성
            </button>
          </form>
        )}

        {projects === null ? (
          <div className="spinner">불러오는 중...</div>
        ) : projects.length === 0 ? (
          <div className="empty-state">아직 참여 중인 프로젝트가 없습니다.</div>
        ) : (
          <div className="card-list">
            {projects.map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`} className="card-link">
                <div className="card">
                  <div className="row">
                    <h3>{p.name}</h3>
                    {p.repo_full_name && <span className="badge">{p.repo_full_name}</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: 32 }}>
        <div className="row">
          <h2>내 팀</h2>
          <button onClick={() => setShowTeamForm((v) => !v)}>
            {showTeamForm ? "취소" : "+ 새 팀"}
          </button>
        </div>

        {showTeamForm && (
          <form onSubmit={handleCreateTeam} className="card stack">
            <div className="field">
              <label>팀 이름</label>
              <input value={teamName} onChange={(e) => setTeamName(e.target.value)} required />
            </div>
            <div className="field">
              <label>타임존 (IANA)</label>
              <input value={teamTimezone} onChange={(e) => setTeamTimezone(e.target.value)} required />
            </div>
            <div className="field">
              <label>국가 (선택)</label>
              <input value={teamCountry} onChange={(e) => setTeamCountry(e.target.value)} />
            </div>
            <div className="field">
              <label>기본 언어</label>
              <select value={teamLanguage} onChange={(e) => setTeamLanguage(e.target.value as "ko" | "en")}>
                <option value="ko">한국어</option>
                <option value="en">English</option>
              </select>
            </div>
            <button type="submit" className="primary">
              생성
            </button>
          </form>
        )}

        {teams === null ? (
          <div className="spinner">불러오는 중...</div>
        ) : teams.length === 0 ? (
          <div className="empty-state">아직 소속된 팀이 없습니다.</div>
        ) : (
          <div className="card-list">
            {teams.map((t) => (
              <Link key={t.id} to={`/teams/${t.id}`} className="card-link">
                <div className="card">
                  <div className="row">
                    <h3>{t.name}</h3>
                    <span className="badge">{t.role === "leader" ? "리더" : "멤버"}</span>
                  </div>
                  <p style={{ fontSize: 13 }}>
                    {t.timezone} · {t.work_start}–{t.work_end}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
