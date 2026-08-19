import { useEffect, useRef, useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { ErrorBanner } from "../components/ErrorBanner";

export function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const { setTokens } = useAuth();
  const { t } = useLanguage();
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ranRef = useRef(false);

  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    if (!accessToken || !refreshToken) {
      setError(t("oauth.noToken"));
      return;
    }
    setTokens(accessToken, refreshToken).then(() => setDone(true));
  }, [params, setTokens, t]);

  if (done) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="page page-narrow">
      <ErrorBanner message={error} />
      {!error && <div className="spinner">{t("oauth.processing")}</div>}
    </div>
  );
}
