import { useState } from "react";
import { Navigate } from "react-router-dom";
import { githubLoginUrl, login } from "../api/auth";
import { demoLogin, seedDemo } from "../api/demo";
import { useAuth } from "../context/AuthContext";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function LoginPage() {
  const { isAuthenticated, setTokens } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handlePasswordLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const tokens = await login(email, password);
      await setTokens(tokens.access_token, tokens.refresh_token);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleDemoLogin() {
    setError(null);
    setBusy(true);
    try {
      try {
        const tokens = await demoLogin();
        await setTokens(tokens.access_token, tokens.refresh_token);
        return;
      } catch {
        // demo account not seeded yet — seed then retry
      }
      await seedDemo();
      const tokens = await demoLogin();
      await setTokens(tokens.access_token, tokens.refresh_token);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page page-narrow">
      <h1>너머에 로그인</h1>
      <p style={{ marginBottom: 24 }}>
        시차를 넘어 팀의 하루를 이어주는 비동기 인수인계 레이어
      </p>

      <div className="card stack">
        <a href={githubLoginUrl()}>
          <button className="primary" style={{ width: "100%" }}>
            GitHub로 로그인
          </button>
        </a>
        <button onClick={handleDemoLogin} disabled={busy} style={{ width: "100%" }}>
          데모 계정으로 체험하기
        </button>
      </div>

      <div className="card">
        <h3>이메일로 로그인</h3>
        <ErrorBanner message={error} />
        <form onSubmit={handlePasswordLogin} className="stack">
          <div className="field">
            <label htmlFor="email">이메일</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">비밀번호</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={busy}>
            로그인
          </button>
        </form>
      </div>
    </div>
  );
}
