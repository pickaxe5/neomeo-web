import { useEffect, useRef, useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ErrorBanner } from "../components/ErrorBanner";

export function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const { setTokens } = useAuth();
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ranRef = useRef(false);

  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    if (!accessToken || !refreshToken) {
      setError("로그인 응답에 토큰이 없습니다.");
      return;
    }
    setTokens(accessToken, refreshToken).then(() => setDone(true));
  }, [params, setTokens]);

  if (done) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="page page-narrow">
      <ErrorBanner message={error} />
      {!error && <div className="spinner">GitHub 로그인 처리 중...</div>}
    </div>
  );
}
