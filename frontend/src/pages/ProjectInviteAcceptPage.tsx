import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { acceptProjectInvite } from "../api/projects";
import { fetchMyTeams } from "../api/me";
import type { MyTeamOut, ProjectInviteAcceptResponse } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";

export function ProjectInviteAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const { isAuthenticated, loading } = useAuth();
  const { t } = useLanguage();
  const [leaderTeams, setLeaderTeams] = useState<MyTeamOut[] | null>(null);
  const [teamId, setTeamId] = useState("");
  const [result, setResult] = useState<ProjectInviteAcceptResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    fetchMyTeams()
      .then((teams) => setLeaderTeams(teams.filter((t2) => t2.role === "leader")))
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

  if (loading) return <div className="spinner">{t("common.loading")}</div>;

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <div className="card">
          <h2>{t("projectInvite.title")}</h2>
          <p>{t("invite.loginRequired")}</p>
          <Link to={`/login?next=/project-invite/${token}`}>
            <button className="primary">{t("invite.goLogin")}</button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page page-narrow">
      <div className="card">
        <h2>{t("projectInvite.title")}</h2>
        <ErrorBanner message={error} />

        {result ? (
          <>
            <p>{t("projectInvite.joinedMessage", { team: result.team.name, project: result.project.name })}</p>
            <Link to={`/projects/${result.project.id}`}>
              <button className="primary">{t("projectInvite.goProject")}</button>
            </Link>
          </>
        ) : leaderTeams === null ? (
          <div className="spinner">{t("common.loading")}</div>
        ) : leaderTeams.length === 0 ? (
          <p>{t("projectInvite.noLeaderTeams")}</p>
        ) : (
          <div className="stack">
            <p>{t("projectInvite.selectTeamPrompt")}</p>
            <div className="field">
              <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
                <option value="">{t("timeline.teamSelectPlaceholder")}</option>
                {leaderTeams.map((t2) => (
                  <option key={t2.id} value={t2.id}>
                    {t2.name}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary" onClick={handleAccept} disabled={!teamId || busy}>
              {t("projectInvite.join")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
