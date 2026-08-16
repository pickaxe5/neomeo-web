import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { acceptInvite } from "../api/teams";
import type { TeamOut } from "../types/api";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";

export function InviteAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const { isAuthenticated, loading } = useAuth();
  const { t } = useLanguage();
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

  if (loading) return <div className="spinner">{t("common.loading")}</div>;

  if (!isAuthenticated) {
    return (
      <div className="page page-narrow">
        <div className="card">
          <h2>{t("invite.teamTitle")}</h2>
          <p>{t("invite.loginRequired")}</p>
          <Link to={`/login?next=/invite/${token}`}>
            <button className="primary">{t("invite.goLogin")}</button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page page-narrow">
      <div className="card">
        <h2>{t("invite.teamTitle")}</h2>
        <ErrorBanner message={error} />
        {busy && <p>{t("invite.processing")}</p>}
        {team && (
          <>
            <p>{t("invite.joinedTeam", { team: team.name })}</p>
            <Link to="/">
              <button className="primary">{t("invite.goDashboard")}</button>
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
