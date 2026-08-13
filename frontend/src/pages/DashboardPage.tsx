import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMyTeams, fetchMyProjects } from "../api/me";
import { createTeam } from "../api/teams";
import { createProject } from "../api/projects";
import type { MyProjectOut, MyTeamOut } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

const INTRO_DISMISSED_KEY = "neomeo_dashboard_intro_dismissed";

export function DashboardPage() {
  const [teams, setTeams] = useState<MyTeamOut[] | null>(null);
  const [projects, setProjects] = useState<MyProjectOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showIntro, setShowIntro] = useState(() => localStorage.getItem(INTRO_DISMISSED_KEY) !== "1");

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
      <h1>대시보드</h1>

      {showIntro && (
        <div className="intro-banner">
          <span className="intro-banner-icon">i</span>
          <div className="intro-banner-body">
            <strong>처음이신가요?</strong>
            <p>
              아래 "내 프로젝트"에서 프로젝트를 클릭하면 상세 화면으로 들어갑니다. 거기서
              <strong> 타임라인</strong>(팀별 업무 종료 카드), <strong>브리핑</strong>(내가 답해야 할 질문),{" "}
              <strong>설정</strong>(GitHub 연동·팀 관리)을 확인할 수 있어요. 프로젝트가 아직 없다면
              "내 팀"에서 팀을 먼저 만들거나, 로그인 화면의 데모 계정으로 예시 데이터를 체험해보세요.
            </p>
          </div>
          <button className="intro-banner-close" onClick={dismissIntro} aria-label="안내 닫기">
            ×
          </button>
        </div>
      )}

      <ErrorBanner message={error} />

      <section>
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
          <div className="list-panel">
            {teams.map((t) => (
              <Link key={t.id} to={`/teams/${t.id}`} className="list-row">
                <span className="list-row-icon">{t.name.slice(0, 1)}</span>
                <span className="list-row-main">
                  <span className="name">{t.name}</span>
                  <span className="sub">
                    {t.timezone} · {t.work_start}–{t.work_end}
                  </span>
                </span>
                <span className="list-row-end">
                  <span className={`badge ${t.role === "leader" ? "accent" : "muted"}`}>
                    {t.role === "leader" ? "리더" : "멤버"}
                  </span>
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: 32 }}>
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
          <div className="list-panel">
            {projects.map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`} className="list-row">
                <span className="list-row-icon">{p.name.slice(0, 1)}</span>
                <span className="list-row-main">
                  <span className="name">{p.name}</span>
                  {p.repo_full_name && <span className="sub">{p.repo_full_name}</span>}
                </span>
                <span className="list-row-end">
                  {p.repo_full_name ? (
                    <span className="badge ok">GitHub 연결</span>
                  ) : (
                    <span className="badge muted">미연결</span>
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
