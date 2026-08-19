import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  fetchProject,
  putProjectDocument,
  uploadProjectDocumentFile,
  addParticipatingTeam,
  fetchParticipatingTeams,
  removeParticipatingTeam,
  updateProject,
  deleteProject,
  createProjectInviteLink,
} from "../api/projects";
import { fetchTimeline, triggerClosure } from "../api/timeline";
import { fetchBriefing } from "../api/briefing";
import { connectGithub, disconnectGithub, fetchGithubStatus, fetchMyGithubRepos } from "../api/github";
import { fetchMyTeams } from "../api/me";
import { useLanguage } from "../i18n/LanguageContext";
import type {
  BriefingOut,
  GithubRepoOut,
  GithubRepoStatusOut,
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
  const { t } = useLanguage();
  const [tab, setTab] = useState<Tab>("timeline");
  const [project, setProject] = useState<ProjectOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    setError(null);
    fetchProject(projectId)
      .then(setProject)
      .catch((err) => setError(errorMessage(err)));
  }, [projectId]);

  if (!projectId) return null;

  return (
    <div className="page">
      <h1>{project?.name ?? t("project.fallbackTitle")}</h1>
      <ErrorBanner message={error} />

      <div className="tabs">
        <button className={tab === "timeline" ? "active" : ""} onClick={() => setTab("timeline")}>
          {t("project.tabTimeline")}
        </button>
        <button className={tab === "briefing" ? "active" : ""} onClick={() => setTab("briefing")}>
          {t("project.tabBriefing")}
        </button>
        <button className={tab === "settings" ? "active" : ""} onClick={() => setTab("settings")}>
          {t("project.tabSettings")}
        </button>
      </div>

      {tab === "timeline" && <TimelineTab projectId={projectId} />}
      {tab === "briefing" && <BriefingTab projectId={projectId} />}
      {tab === "settings" && <SettingsTab projectId={projectId} project={project} onUpdated={setProject} />}
    </div>
  );
}

function TimelineTab({ projectId }: { projectId: string }) {
  const { t } = useLanguage();
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [cards, setCards] = useState<TimelineCardOut[] | null>(null);
  const [teams, setTeams] = useState<MyTeamOut[]>([]);
  const [participatingTeams, setParticipatingTeams] = useState<ParticipatingTeamOut[]>([]);
  const [teamId, setTeamId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reload() {
    setError(null);
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
          <option value="ko">{t("common.korean")}</option>
          <option value="en">{t("common.english")}</option>
        </select>
        <div className="actions">
          <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
            <option value="">{t("timeline.teamSelectPlaceholder")}</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          <button onClick={handleManualClose} disabled={!teamId || busy}>
            {t("timeline.closeNow")}
          </button>
        </div>
      </div>

      <ErrorBanner message={error} />

      {cards === null ? (
        <div className="spinner">{t("common.loading")}</div>
      ) : cards.length === 0 ? (
        <div className="empty-state">{t("timeline.noCards")}</div>
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
  const { t } = useLanguage();
  const [briefing, setBriefing] = useState<BriefingOut | null>(null);
  const [teams, setTeams] = useState<ParticipatingTeamOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    fetchBriefing(projectId)
      .then(setBriefing)
      .catch((err) => setError(errorMessage(err)));
    fetchParticipatingTeams(projectId).then(setTeams).catch(() => {});
  }, [projectId]);

  if (error) return <ErrorBanner message={error} />;
  if (!briefing) return <div className="spinner">{t("common.loading")}</div>;

  return <BriefingPanel briefing={briefing} projectId={projectId} teams={teams} />;
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
  const { t } = useLanguage();
  const [repos, setRepos] = useState<GithubRepoStatusOut[] | null>(null);
  const [repoFullName, setRepoFullName] = useState("");
  const [myRepos, setMyRepos] = useState<GithubRepoOut[] | null>(null);
  const [docContent, setDocContent] = useState("");
  const [docFile, setDocFile] = useState<File | null>(null);
  const [uploadingDoc, setUploadingDoc] = useState(false);
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
    setError(null);
    fetchGithubStatus(projectId)
      .then(setRepos)
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
      setMessage(t("settings.renamedMessage"));
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
    if (!window.confirm(t("settings.deleteConfirm", { name: project.name }))) return;
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
      setRepos(s);
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
      setMessage(t("settings.connectedMessage", { n: result.backfill_event_count }));
      setRepoFullName("");
      const s = await fetchGithubStatus(projectId);
      setRepos(s);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleDisconnect(repoId: string, repoFullNameLabel: string) {
    if (!window.confirm(t("settings.disconnectConfirm", { name: repoFullNameLabel }))) return;
    setError(null);
    try {
      await disconnectGithub(projectId, repoId);
      setRepos((prev) => prev?.filter((r) => r.repo_id !== repoId) ?? prev);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleSaveDocument(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await putProjectDocument(projectId, docContent);
      setMessage(t("settings.savedDocMessage"));
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleUploadDocument(e: React.FormEvent) {
    e.preventDefault();
    if (!docFile) return;
    setError(null);
    setUploadingDoc(true);
    try {
      const updated = await uploadProjectDocumentFile(projectId, docFile);
      setDocContent(updated.content);
      setDocFile(null);
      setMessage(t("settings.savedDocMessage"));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setUploadingDoc(false);
    }
  }

  async function handleAddTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!addTeamId) return;
    setError(null);
    try {
      await addParticipatingTeam(projectId, addTeamId);
      setMessage(t("settings.addedTeamMessage"));
      if (!participatingTeamsUnavailable) {
        fetchParticipatingTeams(projectId)
          .then(setParticipatingTeams)
          .catch(() => setParticipatingTeamsUnavailable(true));
      }
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleRemoveTeam(teamId: string, teamName: string) {
    if (!window.confirm(t("settings.removeTeamConfirm", { name: teamName }))) return;
    setError(null);
    try {
      await removeParticipatingTeam(projectId, teamId);
      setParticipatingTeams((prev) => prev?.filter((tm) => tm.id !== teamId) ?? prev);
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
        <h2>{t("settings.participatingTeams")}</h2>
        {participatingTeams === null && !participatingTeamsUnavailable && (
          <div className="spinner">{t("common.loading")}</div>
        )}
        {participatingTeamsUnavailable && (
          <p className="quick-action-meta">{t("settings.participatingTeamsUnavailable")}</p>
        )}
        {participatingTeams && participatingTeams.length === 0 && (
          <p className="quick-action-meta">{t("settings.noParticipatingTeams")}</p>
        )}
        {participatingTeams && participatingTeams.length > 0 && (
          <div className="list-panel">
            {participatingTeams.map((team) => (
              <div key={team.id} className="list-row">
                <Link to={`/teams/${team.id}`} className="list-row-icon" style={{ textDecoration: "none" }}>
                  {team.name.slice(0, 1)}
                </Link>
                <Link to={`/teams/${team.id}`} className="list-row-main" style={{ textDecoration: "none" }}>
                  <span className="name">{team.name}</span>
                  <span className="sub">
                    {team.country ? `${team.country} · ` : ""}
                    {team.timezone}
                  </span>
                </Link>
                {isAdmin && (
                  <span className="list-row-end">
                    <button
                      className="danger"
                      style={{ padding: "3px 8px", fontSize: 11.5 }}
                      onClick={() => handleRemoveTeam(team.id, team.name)}
                    >
                      {t("settings.removeTeam")}
                    </button>
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {isAdmin && (
        <div className="card">
          <h2>{t("settings.teamInvite")}</h2>
          <p style={{ fontSize: 13 }}>{t("settings.teamInviteHint")}</p>
          <button onClick={handleCreateInvite}>{t("settings.createInviteLink")}</button>
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
            <h3>{t("settings.githubIntegration")}</h3>
            <button
              onClick={handleRefreshStatus}
              disabled={statusBusy}
              style={{ padding: "3px 8px", fontSize: 11.5 }}
            >
              {statusBusy ? t("settings.checking") : t("settings.checkStatus")}
            </button>
          </div>

          {repos && repos.length === 0 && (
            <p className="quick-action-meta">{t("settings.notConnected")}</p>
          )}
          {repos && repos.length > 0 && (
            <div className="stack" style={{ marginBottom: 10 }}>
              {repos.map((r) => (
                <div key={r.repo_id} className="row" style={{ justifyContent: "space-between" }}>
                  <span>
                    <span className={`badge ${r.last_error ? "danger" : "ok"}`} style={{ marginRight: 6 }}>
                      {r.last_error ? t("settings.connectionError") : t("settings.connected")}
                    </span>
                    <a href={`https://github.com/${r.repo_full_name}`} target="_blank" rel="noreferrer">
                      {r.repo_full_name}
                    </a>
                    <span className="quick-action-meta" style={{ display: "block" }}>
                      {r.last_error
                        ? `${t("settings.error")} ${r.last_error}`
                        : r.last_collected_at
                          ? `${t("settings.lastCollected")} ${new Date(r.last_collected_at).toLocaleString()}`
                          : t("settings.firstCollectWaiting")}
                    </span>
                  </span>
                  <button
                    className="danger"
                    style={{ padding: "3px 8px", fontSize: 11.5, flexShrink: 0 }}
                    onClick={() => handleDisconnect(r.repo_id, r.repo_full_name)}
                  >
                    {t("settings.disconnect")}
                  </button>
                </div>
              ))}
            </div>
          )}

          {myRepos && myRepos.length > 0 && (
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) setRepoFullName(e.target.value);
              }}
            >
              <option value="">{t("settings.selectFromRepos")}</option>
              {Object.entries(
                myRepos.reduce<Record<string, GithubRepoOut[]>>((groups, r) => {
                  (groups[r.owner] ??= []).push(r);
                  return groups;
                }, {}),
              ).map(([owner, ownerRepos]) => (
                <optgroup key={owner} label={owner}>
                  {ownerRepos.map((r) => (
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
              {t("settings.connectButton")}
            </button>
          </form>
        </div>

        <div className="quick-action">
          <div className="quick-action-head">
            <h3>{t("settings.addTeam")}</h3>
          </div>
          <form onSubmit={handleAddTeam} className="inline-form">
            <select value={addTeamId} onChange={(e) => setAddTeamId(e.target.value)}>
              <option value="">{t("timeline.teamSelectPlaceholder")}</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <button type="submit">{t("common.add")}</button>
          </form>
        </div>

        <div className="quick-action">
          <div className="quick-action-head">
            <h3>{t("settings.renameProject")}</h3>
          </div>
          <form onSubmit={handleRenameProject} className="inline-form">
            <input value={projectName} onChange={(e) => setProjectName(e.target.value)} />
            <button type="submit">{t("common.change")}</button>
          </form>
          {project && (
            <p className="quick-action-meta">
              {t("settings.createdAt")} {new Date(project.created_at).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <h2>{t("settings.planningDoc")}</h2>
        <form onSubmit={handleSaveDocument} className="stack">
          <textarea
            rows={6}
            value={docContent}
            onChange={(e) => setDocContent(e.target.value)}
            placeholder={t("settings.planningDocPlaceholder")}
          />
          <button type="submit">{t("common.save")}</button>
        </form>

        <div className="doc-upload">
          <label>{t("settings.planningDocUploadLabel")}</label>
          <p className="hint">{t("settings.planningDocUploadHint")}</p>
          <form onSubmit={handleUploadDocument} className="inline-form">
            <label className="file-picker">
              {docFile ? docFile.name : t("settings.planningDocNoFile")}
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt,.md"
                onChange={(e) => setDocFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <button type="submit" disabled={!docFile || uploadingDoc}>
              {uploadingDoc ? t("settings.planningDocUploading") : t("settings.planningDocUploadButton")}
            </button>
          </form>
        </div>
      </div>

      {isAdmin && (
        <div className="card danger-zone">
          <h2>{t("settings.deleteSection")}</h2>
          <div className="danger-row">
            <div>
              <strong>{t("settings.deleteProjectTitle")}</strong>
              <p>{t("settings.deleteProjectDesc")}</p>
            </div>
            <button className="danger" onClick={handleDeleteProject} disabled={busy}>
              {t("common.delete")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
