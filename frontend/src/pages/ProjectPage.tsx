import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchProject, putProjectDocument, addParticipatingTeam, updateProject } from "../api/projects";
import { fetchTimeline, triggerClosure } from "../api/timeline";
import { fetchBriefing } from "../api/briefing";
import { connectGithub, fetchGithubStatus } from "../api/github";
import { fetchMyTeams } from "../api/me";
import type {
  BriefingOut,
  GithubStatusOut,
  MyTeamOut,
  ProjectOut,
  TimelineCardOut,
} from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { TimelineCard } from "../components/TimelineCard";
import { BriefingPanel } from "../components/BriefingPanel";

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
  }, []);

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

  return <BriefingPanel briefing={briefing} />;
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
  const [status, setStatus] = useState<GithubStatusOut | null>(null);
  const [repoFullName, setRepoFullName] = useState("");
  const [docContent, setDocContent] = useState("");
  const [teams, setTeams] = useState<MyTeamOut[]>([]);
  const [addTeamId, setAddTeamId] = useState("");
  const [projectName, setProjectName] = useState(project?.name ?? "");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchGithubStatus(projectId)
      .then(setStatus)
      .catch((err) => setError(errorMessage(err)));
    fetchMyTeams().then(setTeams).catch(() => {});
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

      <div className="quick-actions">
        <div className="quick-action">
          <div className="quick-action-head">
            <h3>GitHub 연동</h3>
            {status && (
              <span className={`badge ${status.connected ? "ok" : "muted"}`}>
                {status.connected ? "연결됨" : "미연결"}
              </span>
            )}
          </div>
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
          {status?.last_collected_at && (
            <p className="quick-action-meta">
              마지막 수집: {new Date(status.last_collected_at).toLocaleString()}
            </p>
          )}
          {status?.last_error && <p className="quick-action-meta">오류: {status.last_error}</p>}
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
    </div>
  );
}
