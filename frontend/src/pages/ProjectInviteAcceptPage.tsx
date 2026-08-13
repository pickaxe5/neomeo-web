import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { acceptProjectInvite } from "../api/projects";
import { fetchMyTeams } from "../api/me";
import type { MyTeamOut, ProjectInviteAcceptResponse } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export function ProjectInviteAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const { isAuthenticated, loading } = useAuth();
  const [leaderTeams, setLeaderTeams] = useState<MyTeamOut[] | null>(null);
  const [teamId, setTeamId] = useState("");
  const [result, setResult] = useState<ProjectInviteAcceptResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    fetchMyTeams()
      .then((teams) => setLeaderTeams(teams.filter((t) => t.role === "leader")))
      .catch((err) => setError(errorMessage(err)));
  }, [isAuthenticated, loading]);

  async function handleAccept() {
    if (!token || !teamId) return;
    setError(null);
    setBusy(true);
    try {
      const res = await acceptProjectInvite(token, teamId);
      setResult(res);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="spinner">불러오는 중...</div>;

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <div className="card">
          <h2>프로젝트 초대</h2>
          <p>초대를 수락하려면 먼저 로그인해야 합니다.</p>
          <Link to={`/login?next=/project-invite/${token}`}>
            <button className="primary">로그인하러 가기</button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page page-narrow">
      <div className="card">
        <h2>프로젝트 초대</h2>
        <ErrorBanner message={error} />

        {result ? (
          <>
            <p>
              <strong>{result.team.name}</strong> 팀이 <strong>{result.project.name}</strong> 프로젝트에
              참여했습니다.
            </p>
            <Link to={`/projects/${result.project.id}`}>
              <button className="primary">프로젝트로 이동</button>
            </Link>
          </>
        ) : leaderTeams === null ? (
          <div className="spinner">불러오는 중...</div>
        ) : leaderTeams.length === 0 ? (
          <p>
            리더인 팀이 없습니다. 팀 리더만 이 초대로 자기 팀을 프로젝트에 참여시킬 수 있습니다.
          </p>
        ) : (
          <div className="stack">
            <p>참여시킬 팀을 선택하세요 (리더인 팀만 표시됩니다).</p>
            <div className="field">
              <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
                <option value="">팀 선택</option>
                {leaderTeams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary" onClick={handleAccept} disabled={!teamId || busy}>
              참여시키기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
