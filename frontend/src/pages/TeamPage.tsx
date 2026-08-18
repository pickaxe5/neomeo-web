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
  updateMemberRole,
  removeMember,
} from "../api/teams";
import { fetchMyTeams } from "../api/me";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { JOB_ROLE_OPTIONS, jobRoleKey } from "../lib/jobRole";
import { COUNTRY_CODES, countryLabel } from "../lib/countries";
import { listTimezones } from "../lib/timezones";
import type { TeamOut, TeamRole, TeamMemberOut, JobRole } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function TeamPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t, lang } = useLanguage();
  const timezoneOptions = listTimezones();
  const [team, setTeam] = useState<TeamOut | null>(null);
  const [myRole, setMyRole] = useState<TeamRole | null>(null);
  const [members, setMembers] = useState<TeamMemberOut[] | null>(null);
  const [membersUnavailable, setMembersUnavailable] = useState(false);
  const [myJobRole, setMyJobRole] = useState<JobRole | "">("");
  const [myJobRoleLabel, setMyJobRoleLabel] = useState("");
  const [myAssignedArea, setMyAssignedArea] = useState("");
  const [assignmentSaved, setAssignmentSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<TeamOut>>({});
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!teamId) return;
    setError(null);
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
          setMyJobRoleLabel(mine.job_role_label ?? "");
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
        job_role_label: myJobRole === "custom" ? myJobRoleLabel || undefined : undefined,
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

  async function handleTransferLeader(targetUserId: string, targetName: string) {
    if (!teamId || !user) return;
    if (!window.confirm(t("team.transferLeaderConfirm", { name: targetName }))) return;
    setError(null);
    setBusy(true);
    try {
      // "위임"은 대상을 리더로 올리는 것과 내가 리더에서 내려오는 것, 두 번의 역할 변경으로
      // 이뤄진다. 순서가 중요하다 — 먼저 대상을 리더로 올려 리더가 2명이 된 상태를 만들어야,
      // 내가 스스로를 내릴 때 "마지막 리더는 내려올 수 없다" 제약에 걸리지 않는다.
      await updateMemberRole(teamId, targetUserId, { role: "leader" });
      await updateMemberRole(teamId, user.id, { role: "member" });
      const rows = await fetchTeamMembers(teamId);
      setMembers(rows);
      setMyRole("member");
    } catch (err) {
      setError(errorMessage(err));
      const rows = await fetchTeamMembers(teamId).catch(() => null);
      if (rows) setMembers(rows);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemoveMember(targetUserId: string, targetName: string) {
    if (!teamId) return;
    if (!window.confirm(t("team.removeMemberConfirm", { name: targetName }))) return;
    setError(null);
    setBusy(true);
    try {
      await removeMember(teamId, targetUserId);
      setMembers((prev) => prev?.filter((m) => m.user_id !== targetUserId) ?? prev);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
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
              <select
                value={form.timezone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
              >
                {timezoneOptions.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>{t("team.country")}</label>
              <select
                value={form.country ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
              >
                <option value="">{t("common.none")}</option>
                {COUNTRY_CODES.map((code) => (
                  <option key={code} value={code}>
                    {countryLabel(code, lang)}
                  </option>
                ))}
              </select>
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
                const displayName = m.github_handle ? `@${m.github_handle}` : m.name ?? t("team.noName");
                const canManage = myRole === "leader" && m.user_id !== user?.id;
                return (
                  <div key={m.user_id} className="list-row" style={{ cursor: "default" }}>
                    {m.github_handle ? (
                      <img
                        className="list-row-icon list-row-avatar"
                        src={`https://github.com/${m.github_handle}.png?size=64`}
                        alt=""
                      />
                    ) : (
                      <span className="list-row-icon">{(m.name ?? "?").slice(0, 1).toUpperCase()}</span>
                    )}
                    <span className="list-row-main">
                      <span className="name">{displayName}</span>
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
                      {m.job_role && (
                        <span className="badge muted">
                          {m.job_role === "custom" && m.job_role_label
                            ? m.job_role_label
                            : t(jobRoleKey(m.job_role))}
                        </span>
                      )}
                      <span className={`badge ${m.role === "leader" ? "accent" : "muted"}`}>
                        {m.role === "leader" ? t("common.leader") : t("common.member")}
                      </span>
                      {canManage && (
                        <>
                          {m.role === "member" && (
                            <button
                              style={{ padding: "3px 8px", fontSize: 11.5 }}
                              disabled={busy}
                              onClick={() => handleTransferLeader(m.user_id, displayName)}
                            >
                              {t("team.transferLeader")}
                            </button>
                          )}
                          <button
                            className="danger"
                            style={{ padding: "3px 8px", fontSize: 11.5 }}
                            disabled={busy}
                            onClick={() => handleRemoveMember(m.user_id, displayName)}
                          >
                            {t("team.removeMember")}
                          </button>
                        </>
                      )}
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
            {myJobRole === "custom" && (
              <div className="field">
                <label>{t("team.roleCustomLabel")}</label>
                <input
                  value={myJobRoleLabel}
                  onChange={(e) => setMyJobRoleLabel(e.target.value)}
                  placeholder={t("team.roleCustomLabelPlaceholder")}
                  required
                />
              </div>
            )}
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
