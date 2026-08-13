import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { acceptInvite } from "../api/teams";
import type { TeamOut } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export function InviteAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const { isAuthenticated, loading } = useAuth();
  const [team, setTeam] = useState<TeamOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated || !token) return;
    setBusy(true);
    acceptInvite(token)
      .then((res) => setTeam(res.team))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setBusy(false));
  }, [token, isAuthenticated, loading]);

  if (loading) return <div className="spinner">불러오는 중...</div>;

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <div className="card">
          <h2>팀 초대</h2>
          <p>초대를 수락하려면 먼저 로그인해야 합니다.</p>
          <Link to={`/login?next=/invite/${token}`}>
            <button className="primary">로그인하러 가기</button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page page-narrow">
      <div className="card">
        <h2>팀 초대</h2>
        <ErrorBanner message={error} />
        {busy && <p>초대를 처리하는 중...</p>}
        {team && (
          <>
            <p>
              <strong>{team.name}</strong> 팀에 합류했습니다.
            </p>
            <Link to="/">
              <button className="primary">대시보드로 이동</button>
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
