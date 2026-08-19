import { useState } from "react";
import { Navigate } from "react-router-dom";
import { githubLoginUrl, login, signup } from "../api/auth";
import { demoLogin, seedDemo } from "../api/demo";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { ErrorBanner, errorMessage } from "../components/ErrorBanner";

export function LoginPage() {
  const { isAuthenticated, setTokens } = useAuth();
  const { t } = useLanguage();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
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

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const tokens = await signup({ email, password, name: name || undefined });
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

  function switchMode(next: "login" | "signup") {
    setMode(next);
    setError(null);
  }

  return (
    <div className="page page-narrow">
      <h1>{t("login.title")}</h1>
      <p style={{ marginBottom: 24 }}>{t("login.subtitle")}</p>

      <div className="card stack">
        <div>
          <a href={githubLoginUrl()}>
            <button className="primary" style={{ width: "100%" }}>
              {t("login.githubButton")}
            </button>
          </a>
          <p className="hint">{t("login.githubHint")}</p>
        </div>
        <div>
          <button onClick={handleDemoLogin} disabled={busy} style={{ width: "100%" }}>
            {t("login.demoButton")}
          </button>
          <p className="hint">{t("login.demoHint")}</p>
        </div>
      </div>

      <div className="card">
        <div className="tabs" style={{ marginBottom: 16 }}>
          <button className={mode === "login" ? "active" : ""} onClick={() => switchMode("login")}>
            {t("login.tabLogin")}
          </button>
          <button className={mode === "signup" ? "active" : ""} onClick={() => switchMode("signup")}>
            {t("login.tabSignup")}
          </button>
        </div>

        <ErrorBanner message={error} />

        {mode === "login" ? (
          <form onSubmit={handlePasswordLogin} className="stack">
            <div className="field">
              <label htmlFor="email">{t("login.emailLabel")}</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="password">{t("login.passwordLabel")}</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={busy}>
              {t("login.loginButton")}
            </button>
          </form>
        ) : (
          <form onSubmit={handleSignup} className="stack">
            <div className="field">
              <label htmlFor="signup-email">{t("login.emailLabel")}</label>
              <input
                id="signup-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="signup-password">{t("login.passwordLabel")}</label>
              <input
                id="signup-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="signup-name">{t("login.nameLabel")}</label>
              <input id="signup-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <button type="submit" className="primary" disabled={busy}>
              {t("login.signupButton")}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
