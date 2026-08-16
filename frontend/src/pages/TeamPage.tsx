import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  fetchTeam,
  updateTeam,
  createInviteLink,
  deleteTeam,
  leaveTeam,
  fetchTeamMembers,
  updateMyAssignment,
} from "../api/teams";
import { fetchMyTeams } from "../api/me";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { JOB_ROLE_OPTIONS, jobRoleKey } from "../lib/jobRole";
import type { TeamOut, TeamRole, TeamMemberOut, JobRole } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function TeamPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();
  const [team, setTeam] = useState<TeamOut | null>(null);
  const [myRole, setMyRole] = useState<TeamRole | null>(null);
  const [members, setMembers] = useState<TeamMemberOut[] | null>(null);
  const [membersUnavailable, setMembersUnavailable] = useState(false);
  const [myJobRole, setMyJobRole] = useState<JobRole | "">("");
  const [myAssignedArea, setMyAssignedArea] = useState("");
  const [assignmentSaved, setAssignmentSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<TeamOut>>({});
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!teamId) return;
    fetchTeam(teamId)
      .then((t2) => {
        setTeam(t2);
        setForm(t2);
      })
      .catch((err) => setError(errorMessage(err)));
    fetchMyTeams()
      .then((teams) => setMyRole(teams.find((t2) => t2.id === teamId)?.role ?? null))
      .catch(() => {});
    // 팀 멤버만 조회 가능(403) — 소속이 아니면 조용히 섹션을 숨긴다.
    fetchTeamMembers(teamId)
      .then((rows) => {
        setMembers(rows);
        const mine = rows.find((m) => m.user_id === user?.id);
        if (mine) {
          setMyJobRole(mine.job_role ?? "");
          setMyAssignedArea(mine.assigned_area ?? "");
        }
      })
      .catch(() => setMembersUnavailable(true));
  }, [teamId, user?.id]);

  async function handleSaveAssignment(e: React.FormEvent) {
    e.preventDefault();
    if (!teamId) return;
    setError(null);
    setAssignmentSaved(false);
    try {
      const updated = await updateMyAssignment(teamId, {
        job_role: myJobRole || undefined,
        assigned_area: myAssignedArea || undefined,
      });
      setMembers((prev) => prev?.map((m) => (m.user_id === updated.user_id ? updated : m)) ?? prev);
      setAssignmentSaved(true);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!teamId) return;
    setError(null);
    try {
      const updated = await updateTeam(teamId, {
        name: form.name,
        country: form.country ?? undefined,
        timezone: form.timezone,
        work_start: form.work_start,
        work_end: form.work_end,
        default_language: form.default_language,
      });
      setTeam(updated);
      setEditing(false);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleInvite() {
    if (!teamId) return;
    setError(null);
    try {
      const invite = await createInviteLink(teamId);
      setInviteUrl(`${window.location.origin}/invite/${invite.token}`);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleLeave() {
    if (!teamId || !team) return;
    if (!window.confirm(t("team.leaveConfirm", { name: team.name }))) return;
    setError(null);
    setBusy(true);
    try {
      await leaveTeam(teamId);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!teamId || !team) return;
    if (!window.confirm(t("team.deleteConfirm", { name: team.name }))) return;
    setError(null);
    setBusy(true);
    try {
      await deleteTeam(teamId);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  if (!team) {
    return (
      <div className="page">
        <ErrorBanner message={error} />
        {!error && <div className="spinner">{t("common.loading")}</div>}
      </div>
    );
  }

  return (
    <div className="page">
      <h1>{team.name}</h1>
      <ErrorBanner message={error} />

      <div className="card">
        <div className="row">
          <h2>{t("team.settings")}</h2>
          <button onClick={() => setEditing((v) => !v)}>{editing ? t("common.cancel") : t("common.edit")}</button>
        </div>

        {editing ? (
          <form onSubmit={handleSave} className="stack">
            <div className="field">
              <label>{t("team.teamName")}</label>
              <input
                value={form.name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>{t("team.timezone")}</label>
              <input
                value={form.timezone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>{t("team.country")}</label>
              <input
                value={form.country ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
              />
            </div>
            <div className="row">
              <div className="field" style={{ flex: 1 }}>
                <label>{t("team.workStart")}</label>
                <input
                  type="time"
                  value={form.work_start ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, work_start: e.target.value }))}
                />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>{t("team.workEnd")}</label>
                <input
                  type="time"
                  value={form.work_end ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, work_end: e.target.value }))}
                />
              </div>
            </div>
            <div className="field">
              <label>{t("team.defaultLanguage")}</label>
              <select
                value={form.default_language ?? "ko"}
                onChange={(e) =>
                  setForm((f) => ({ ...f, default_language: e.target.value as "ko" | "en" }))
                }
              >
                <option value="ko">{t("common.korean")}</option>
                <option value="en">{t("common.english")}</option>
              </select>
            </div>
            <button type="submit" className="primary">
              {t("common.save")}
            </button>
          </form>
        ) : (
          <div className="stack">
            <p>
              {t("team.countryDisplay")} {team.country ?? "-"}
            </p>
            <p>
              {t("team.timezoneDisplay")} {team.timezone}
            </p>
            <p>
              {t("team.workHoursDisplay")} {team.work_start} – {team.work_end}
            </p>
            <p>
              {t("team.defaultLanguageDisplay")}{" "}
              {team.default_language === "ko" ? t("common.korean") : t("common.english")}
            </p>
          </div>
        )}
      </div>

      {!membersUnavailable && (
        <div className="card">
          <h2>{t("team.members")}</h2>
          {members === null && <div className="spinner">{t("common.loading")}</div>}
          {members && members.length === 0 && <p className="quick-action-meta">{t("team.noMembers")}</p>}
          {members && members.length > 0 && (
            <div className="list-panel">
              {members.map((m) => {
                const areaText =
                  m.assigned_area || (m.assigned_paths && m.assigned_paths.length > 0
                    ? m.assigned_paths.join(", ")
                    : null);
                return (
                  <div key={m.user_id} className="list-row" style={{ cursor: "default" }}>
                    <span className="list-row-icon">
                      {(m.github_handle ?? m.name ?? "?").slice(0, 1).toUpperCase()}
                    </span>
                    <span className="list-row-main">
                      <span className="name">
                        {m.github_handle ? `@${m.github_handle}` : m.name ?? t("team.noName")}
                      </span>
                      <span className="sub">
                        {areaText ? (
                          <>
                            {areaText}
                            {!m.assigned_area_confirmed && t("team.estimated")}
                          </>
                        ) : (
                          t("team.noAssignedArea")
                        )}
                      </span>
                    </span>
                    <span className="list-row-end">
                      {m.job_role && <span className="badge muted">{t(jobRoleKey(m.job_role))}</span>}
                      <span className={`badge ${m.role === "leader" ? "accent" : "muted"}`}>
                        {m.role === "leader" ? t("common.leader") : t("common.member")}
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {!membersUnavailable && myRole && (
        <div className="card">
          <h2>{t("team.myRole")}</h2>
          <p style={{ fontSize: 13 }}>{t("team.myRoleHint")}</p>
          <form onSubmit={handleSaveAssignment} className="stack">
            <div className="field">
              <label>{t("team.role")}</label>
              <select value={myJobRole} onChange={(e) => setMyJobRole(e.target.value as JobRole | "")}>
                <option value="">{t("team.roleNone")}</option>
                {JOB_ROLE_OPTIONS.map((r) => (
                  <option key={r} value={r}>
                    {t(jobRoleKey(r))}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>{t("team.assignedArea")}</label>
              <input
                value={myAssignedArea}
                onChange={(e) => setMyAssignedArea(e.target.value)}
                placeholder={t("team.assignedAreaPlaceholder")}
              />
            </div>
            <button type="submit">{t("common.save")}</button>
            {assignmentSaved && <span className="badge ok">{t("team.savedBadge")}</span>}
          </form>
        </div>
      )}

      <div className="card">
        <h2>{t("team.inviteMembers")}</h2>
        <p style={{ fontSize: 13 }}>{t("team.inviteHint")}</p>
        <button onClick={handleInvite}>{t("team.createInviteLink")}</button>
        {inviteUrl && (
          <div className="field" style={{ marginTop: 12 }}>
            <input readOnly value={inviteUrl} onFocus={(e) => e.target.select()} />
          </div>
        )}
      </div>

      {myRole && (
        <div className="card danger-zone">
          <h2>{t("team.dangerZone")}</h2>
          {myRole === "member" && (
            <div className="danger-row">
              <div>
                <strong>{t("team.leaveTeam")}</strong>
                <p>{t("team.leaveTeamDesc")}</p>
              </div>
              <button onClick={handleLeave} disabled={busy}>
                {t("team.leave")}
              </button>
            </div>
          )}
          {myRole === "leader" && (
            <div className="danger-row">
              <div>
                <strong>{t("team.deleteTeam")}</strong>
                <p>{t("team.deleteTeamDesc")}</p>
              </div>
              <button className="danger" onClick={handleDelete} disabled={busy}>
                {t("common.delete")}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
