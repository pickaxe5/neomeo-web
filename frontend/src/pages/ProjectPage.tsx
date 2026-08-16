import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  fetchProject,
  putProjectDocument,
  addParticipatingTeam,
  fetchParticipatingTeams,
  updateProject,
  deleteProject,
  createProjectInviteLink,
} from "../api/projects";
import { fetchTimeline, triggerClosure } from "../api/timeline";
import { fetchBriefing } from "../api/briefing";
import { connectGithub, fetchGithubStatus, fetchMyGithubRepos } from "../api/github";
import { fetchMyTeams } from "../api/me";
import type {
  BriefingOut,
  GithubRepoOut,
  GithubStatusOut,
  MyTeamOut,
  ParticipatingTeamOut,
  ProjectOut,
  TimelineCardOut,
} from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { TimelineCard } from "../components/TimelineCard";
import { BriefingPanel } from "../components/BriefingPanel";
import { TeamStatusBar } from "../components/TeamStatusBar";

type Tab = "timeline" | "briefing" | "settings";

export function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [tab, setTab] = useState<Tab>("timeline");
  const [project, setProject] = useState<ProjectOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    fetchProject(projectId)
      .then(setProject)
      .catch((err) => setError(errorMessage(err)));
  }, [projectId]);

  if (!projectId) return null;

  return (
    <div className="page">
      <h1>{project?.name ?? "프로젝트"}</h1>
      <ErrorBanner message={error} />

      <div className="tabs">
        <button className={tab === "timeline" ? "active" : ""} onClick={() => setTab("timeline")}>
          타임라인
        </button>
        <button className={tab === "briefing" ? "active" : ""} onClick={() => setTab("briefing")}>
          브리핑
        </button>
        <button className={tab === "settings" ? "active" : ""} onClick={() => setTab("settings")}>
          설정
        </button>
      </div>

      {tab === "timeline" && <TimelineTab projectId={projectId} />}
      {tab === "briefing" && <BriefingTab projectId={projectId} />}
      {tab === "settings" && <SettingsTab projectId={projectId} project={project} onUpdated={setProject} />}
    </div>
  );
}

function TimelineTab({ projectId }: { projectId: string }) {
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [cards, setCards] = useState<TimelineCardOut[] | null>(null);
  const [teams, setTeams] = useState<MyTeamOut[]>([]);
  const [participatingTeams, setParticipatingTeams] = useState<ParticipatingTeamOut[]>([]);
  const [teamId, setTeamId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reload() {
    fetchTimeline(projectId, language)
      .then((data) => setCards([...data].reverse()))
      .catch((err) => setError(errorMessage(err)));
  }

  useEffect(reload, [projectId, language]);
  useEffect(() => {
    fetchMyTeams().then(setTeams).catch(() => {});
    fetchParticipatingTeams(projectId).then(setParticipatingTeams).catch(() => {});
  }, [projectId]);

  async function handleManualClose() {
    if (!teamId) return;
    setError(null);
    setBusy(true);
    try {
      await triggerClosure(projectId, teamId, language);
      reload();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <TeamStatusBar teams={participatingTeams} />

      <div className="row" style={{ marginBottom: 16 }}>
        <select value={language} onChange={(e) => setLanguage(e.target.value as "ko" | "en")}>
          <option value="ko">한국어</option>
          <option value="en">English</option>
        </select>
        <div className="actions">
          <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
            <option value="">팀 선택</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <button onClick={handleManualClose} disabled={!teamId || busy}>
            지금 마감하기
          </button>
        </div>
      </div>

      <ErrorBanner message={error} />

      {cards === null ? (
        <div className="spinner">불러오는 중...</div>
      ) : cards.length === 0 ? (
        <div className="empty-state">아직 생성된 카드가 없습니다.</div>
      ) : (
        <div className="timeline">
          {cards.map((c) => (
            <TimelineCard key={c.closure_run_id} card={c} />
          ))}
        </div>
      )}
    </div>
  );
}

function BriefingTab({ projectId }: { projectId: string }) {
  const [briefing, setBriefing] = useState<BriefingOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBriefing(projectId)
      .then(setBriefing)
      .catch((err) => setError(errorMessage(err)));
  }, [projectId]);

  if (error) return <ErrorBanner message={error} />;
  if (!briefing) return <div className="spinner">불러오는 중...</div>;

  return <BriefingPanel briefing={briefing} projectId={projectId} />;
}

function SettingsTab({
  projectId,
  project,
  onUpdated,
}: {
  projectId: string;
  project: ProjectOut | null;
  onUpdated: (p: ProjectOut) => void;
}) {
  const navigate = useNavigate();
  const [status, setStatus] = useState<GithubStatusOut | null>(null);
  const [repoFullName, setRepoFullName] = useState("");
  const [myRepos, setMyRepos] = useState<GithubRepoOut[] | null>(null);
  const [docContent, setDocContent] = useState("");
  const [teams, setTeams] = useState<MyTeamOut[]>([]);
  const [addTeamId, setAddTeamId] = useState("");
  const [participatingTeams, setParticipatingTeams] = useState<ParticipatingTeamOut[] | null>(null);
  const [participatingTeamsUnavailable, setParticipatingTeamsUnavailable] = useState(false);
  const [projectName, setProjectName] = useState(project?.name ?? "");
  const isAdmin = project?.is_admin === true;
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [statusBusy, setStatusBusy] = useState(false);

  useEffect(() => {
    fetchGithubStatus(projectId)
      .then(setStatus)
      .catch((err) => setError(errorMessage(err)));
    fetchMyTeams().then(setTeams).catch(() => {});
    // GitHub 계정 미연동 사용자는 빈 배열이 정상 응답 — 드롭다운을 숨기고 수동 입력만 남긴다.
    fetchMyGithubRepos()
      .then(setMyRepos)
      .catch(() => setMyRepos(null));
    fetchParticipatingTeams(projectId)
      .then(setParticipatingTeams)
      .catch(() => setParticipatingTeamsUnavailable(true));
  }, [projectId]);

  useEffect(() => {
    if (project) setProjectName(project.name);
  }, [project]);

  async function handleRenameProject(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const updated = await updateProject(projectId, projectName);
      onUpdated(updated);
      setMessage("프로젝트 이름을 변경했습니다.");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleCreateInvite() {
    setError(null);
    try {
      const invite = await createProjectInviteLink(projectId);
      setInviteUrl(`${window.location.origin}/project-invite/${invite.token}`);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleDeleteProject() {
    if (!project) return;
    if (!window.confirm(`"${project.name}" 프로젝트를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) return;
    setError(null);
    setBusy(true);
    try {
      await deleteProject(projectId);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  async function handleRefreshStatus() {
    setError(null);
    setStatusBusy(true);
    try {
      const s = await fetchGithubStatus(projectId);
      setStatus(s);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setStatusBusy(false);
    }
  }

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const result = await connectGithub(projectId, repoFullName);
      setMessage(`연동 완료 · 이벤트 ${result.backfill_event_count}건 수집`);
      const s = await fetchGithubStatus(projectId);
      setStatus(s);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveDocument(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await putProjectDocument(projectId, docContent);
      setMessage("기획 문서를 저장했습니다.");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleAddTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!addTeamId) return;
    setError(null);
    try {
      await addParticipatingTeam(projectId, addTeamId);
      setMessage("팀을 프로젝트에 추가했습니다.");
      if (!participatingTeamsUnavailable) {
        fetchParticipatingTeams(projectId)
          .then(setParticipatingTeams)
          .catch(() => setParticipatingTeamsUnavailable(true));
      }
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div className="stack">
      <ErrorBanner message={error} />
      {message && (
        <div className="badge ok" style={{ marginBottom: 4 }}>
          {message}
        </div>
      )}

      <div className="card">
        <h2>참여 팀</h2>
        {participatingTeams === null && !participatingTeamsUnavailable && (
          <div className="spinner">불러오는 중...</div>
        )}
        {participatingTeamsUnavailable && (
          <p className="quick-action-meta">참여 팀 목록을 불러오지 못했습니다.</p>
        )}
        {participatingTeams && participatingTeams.length === 0 && (
          <p className="quick-action-meta">아직 참여 중인 팀이 없습니다.</p>
        )}
        {participatingTeams && participatingTeams.length > 0 && (
          <div className="list-panel">
            {participatingTeams.map((t) => (
              <Link key={t.id} to={`/teams/${t.id}`} className="list-row">
                <span className="list-row-icon">{t.name.slice(0, 1)}</span>
                <span className="list-row-main">
                  <span className="name">{t.name}</span>
                  <span className="sub">
                    {t.country ? `${t.country} · ` : ""}
                    {t.timezone}
                  </span>
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {isAdmin && (
        <div className="card">
          <h2>팀 초대</h2>
          <p style={{ fontSize: 13 }}>
            초대 링크를 받은 사람이 자기 팀(리더인 팀)을 골라 참여시킬 수 있습니다.
          </p>
          <button onClick={handleCreateInvite}>초대 링크 생성</button>
          {inviteUrl && (
            <div className="field" style={{ marginTop: 12 }}>
              <input readOnly value={inviteUrl} onFocus={(e) => e.target.select()} />
            </div>
          )}
        </div>
      )}

      <div className="quick-actions">
        <div className="quick-action">
          <div className="quick-action-head">
            <h3>GitHub 연동</h3>
            <span className="actions" style={{ gap: 6 }}>
              {status && (
                <span
                  className={`badge ${
                    !status.connected ? "muted" : status.last_error ? "danger" : "ok"
                  }`}
                >
                  {!status.connected ? "미연결" : status.last_error ? "연결 오류" : "연결됨"}
                </span>
              )}
              <button
                onClick={handleRefreshStatus}
                disabled={statusBusy}
                style={{ padding: "3px 8px", fontSize: 11.5 }}
              >
                {statusBusy ? "확인 중..." : "상태 확인"}
              </button>
            </span>
          </div>
          {status?.connected && project?.repo_full_name && (
            <p className="quick-action-meta">
              연결된 레포:{" "}
              <a href={`https://github.com/${project.repo_full_name}`} target="_blank" rel="noreferrer">
                {project.repo_full_name}
              </a>
            </p>
          )}
          {myRepos && myRepos.length > 0 && (
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) setRepoFullName(e.target.value);
              }}
            >
              <option value="">내 레포/조직에서 선택...</option>
              {Object.entries(
                myRepos.reduce<Record<string, GithubRepoOut[]>>((groups, r) => {
                  (groups[r.owner] ??= []).push(r);
                  return groups;
                }, {}),
              ).map(([owner, repos]) => (
                <optgroup key={owner} label={owner}>
                  {repos.map((r) => (
                    <option key={r.full_name} value={r.full_name}>
                      {r.full_name}
                      {r.private ? " (private)" : ""}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          )}
          <form onSubmit={handleConnect} className="inline-form">
            <input
              placeholder="owner/repo"
              value={repoFullName}
              onChange={(e) => setRepoFullName(e.target.value)}
              required
            />
            <button type="submit" className="primary" disabled={busy}>
              연결
            </button>
          </form>
          {status?.connected && !status.last_collected_at && !status.last_error && (
            <p className="quick-action-meta">첫 수집 대기 중 (최대 10분 소요)</p>
          )}
          {status?.last_collected_at && (
            <p className="quick-action-meta">
              마지막 수집: {new Date(status.last_collected_at).toLocaleString()}
            </p>
          )}
          {status?.last_error && (
            <p className="quick-action-meta" style={{ color: "var(--danger)" }}>
              오류: {status.last_error}
            </p>
          )}
        </div>

        <div className="quick-action">
          <div className="quick-action-head">
            <h3>참여 팀 추가</h3>
          </div>
          <form onSubmit={handleAddTeam} className="inline-form">
            <select value={addTeamId} onChange={(e) => setAddTeamId(e.target.value)}>
              <option value="">팀 선택</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <button type="submit">추가</button>
          </form>
        </div>

        <div className="quick-action">
          <div className="quick-action-head">
            <h3>이름 변경</h3>
          </div>
          <form onSubmit={handleRenameProject} className="inline-form">
            <input value={projectName} onChange={(e) => setProjectName(e.target.value)} />
            <button type="submit">변경</button>
          </form>
          {project && (
            <p className="quick-action-meta">
              생성일 {new Date(project.created_at).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <h2>기획 문서 (AI 컨텍스트)</h2>
        <form onSubmit={handleSaveDocument} className="stack">
          <textarea
            rows={6}
            value={docContent}
            onChange={(e) => setDocContent(e.target.value)}
            placeholder="프로젝트 배경, 목표 등을 입력하면 카드 생성 품질에 활용됩니다."
          />
          <button type="submit">저장</button>
        </form>
      </div>

      {isAdmin && (
        <div className="card danger-zone">
          <h2>삭제</h2>
          <div className="danger-row">
            <div>
              <strong>프로젝트 삭제</strong>
              <p>프로젝트와 타임라인 카드, GitHub 연동 정보를 모두 삭제합니다. 되돌릴 수 없습니다.</p>
            </div>
            <button className="danger" onClick={handleDeleteProject} disabled={busy}>
              삭제
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
