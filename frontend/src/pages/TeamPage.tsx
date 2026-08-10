import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchTeam, updateTeam, createInviteLink } from "../api/teams";
import type { TeamOut } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function TeamPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const [team, setTeam] = useState<TeamOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<TeamOut>>({});
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!teamId) return;
    fetchTeam(teamId)
      .then((t) => {
        setTeam(t);
        setForm(t);
      })
      .catch((err) => setError(errorMessage(err)));
  }, [teamId]);

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
    </div>
  );
}
