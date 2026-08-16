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
import { JOB_ROLE_LABELS, JOB_ROLE_OPTIONS } from "../lib/jobRole";
import type { TeamOut, TeamRole, TeamMemberOut, JobRole } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function TeamPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
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
      .then((t) => {
        setTeam(t);
        setForm(t);
      })
      .catch((err) => setError(errorMessage(err)));
    fetchMyTeams()
      .then((teams) => setMyRole(teams.find((t) => t.id === teamId)?.role ?? null))
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
    if (!window.confirm(`"${team.name}" 팀에서 나가시겠습니까?`)) return;
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
    if (!window.confirm(`"${team.name}" 팀을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) return;
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
        {!error && <div className="spinner">불러오는 중...</div>}
      </div>
    );
  }

  return (
    <div className="page">
      <h1>{team.name}</h1>
      <ErrorBanner message={error} />

      <div className="card">
        <div className="row">
          <h2>팀 설정</h2>
          <button onClick={() => setEditing((v) => !v)}>{editing ? "취소" : "수정"}</button>
        </div>

        {editing ? (
          <form onSubmit={handleSave} className="stack">
            <div className="field">
              <label>팀 이름</label>
              <input
                value={form.name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>타임존</label>
              <input
                value={form.timezone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>국가</label>
              <input
                value={form.country ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
              />
            </div>
            <div className="row">
              <div className="field" style={{ flex: 1 }}>
                <label>업무 시작</label>
                <input
                  type="time"
                  value={form.work_start ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, work_start: e.target.value }))}
                />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>업무 종료</label>
                <input
                  type="time"
                  value={form.work_end ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, work_end: e.target.value }))}
                />
              </div>
            </div>
            <div className="field">
              <label>기본 언어</label>
              <select
                value={form.default_language ?? "ko"}
                onChange={(e) =>
                  setForm((f) => ({ ...f, default_language: e.target.value as "ko" | "en" }))
                }
              >
                <option value="ko">한국어</option>
                <option value="en">English</option>
              </select>
            </div>
            <button type="submit" className="primary">
              저장
            </button>
          </form>
        ) : (
          <div className="stack">
            <p>국가: {team.country ?? "-"}</p>
            <p>타임존: {team.timezone}</p>
            <p>
              업무 시간: {team.work_start} – {team.work_end}
            </p>
            <p>기본 언어: {team.default_language === "ko" ? "한국어" : "English"}</p>
          </div>
        )}
      </div>

      {!membersUnavailable && (
        <div className="card">
          <h2>팀원</h2>
          {members === null && <div className="spinner">불러오는 중...</div>}
          {members && members.length === 0 && (
            <p className="quick-action-meta">아직 팀원이 없습니다.</p>
          )}
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
                        {m.github_handle ? `@${m.github_handle}` : m.name ?? "이름 없음"}
                      </span>
                      <span className="sub">
                        {areaText ? (
                          <>
                            {areaText}
                            {!m.assigned_area_confirmed && " (추정)"}
                          </>
                        ) : (
                          "담당 영역 미설정"
                        )}
                      </span>
                    </span>
                    <span className="list-row-end">
                      {m.job_role && <span className="badge muted">{JOB_ROLE_LABELS[m.job_role]}</span>}
                      <span className={`badge ${m.role === "leader" ? "accent" : "muted"}`}>
                        {m.role === "leader" ? "리더" : "멤버"}
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
          <h2>내 역할</h2>
          <p style={{ fontSize: 13 }}>
            담당 영역을 직접 입력하면, 커밋 기반 자동 추정값 대신 이 값이 우선 표시됩니다.
          </p>
          <form onSubmit={handleSaveAssignment} className="stack">
            <div className="field">
              <label>역할</label>
              <select value={myJobRole} onChange={(e) => setMyJobRole(e.target.value as JobRole | "")}>
                <option value="">선택 안 함</option>
                {JOB_ROLE_OPTIONS.map((r) => (
                  <option key={r} value={r}>
                    {JOB_ROLE_LABELS[r]}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>담당 영역</label>
              <input
                value={myAssignedArea}
                onChange={(e) => setMyAssignedArea(e.target.value)}
                placeholder="예: 로그인/결제 플로우"
              />
            </div>
            <button type="submit">저장</button>
            {assignmentSaved && <span className="badge ok">저장됨</span>}
          </form>
        </div>
      )}

      <div className="card">
        <h2>팀원 초대</h2>
        <p style={{ fontSize: 13 }}>초대 링크는 30일간 유효합니다. (리더만 생성 가능)</p>
        <button onClick={handleInvite}>초대 링크 생성</button>
        {inviteUrl && (
          <div className="field" style={{ marginTop: 12 }}>
            <input readOnly value={inviteUrl} onFocus={(e) => e.target.select()} />
          </div>
        )}
      </div>

      {myRole && (
        <div className="card danger-zone">
          <h2>탈퇴 및 삭제</h2>
          {myRole === "member" && (
            <div className="danger-row">
              <div>
                <strong>팀 나가기</strong>
                <p>이 팀에서 내 멤버십만 제거합니다. 다른 팀원에게는 영향이 없습니다.</p>
              </div>
              <button onClick={handleLeave} disabled={busy}>
                나가기
              </button>
            </div>
          )}
          {myRole === "leader" && (
            <div className="danger-row">
              <div>
                <strong>팀 삭제</strong>
                <p>팀과 소속 멤버십을 모두 삭제합니다. 되돌릴 수 없습니다.</p>
              </div>
              <button className="danger" onClick={handleDelete} disabled={busy}>
                삭제
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
