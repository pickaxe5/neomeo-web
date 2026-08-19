import { Route, Routes, useLocation } from "react-router-dom";
import "./App.css";
import { Navbar } from "./components/Navbar";
import { AppShell } from "./components/AppShell";
import { SkyBackground } from "./components/SkyBackground";
import { useAuth } from "./context/AuthContext";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { TeamPage } from "./pages/TeamPage";
import { InviteAcceptPage } from "./pages/InviteAcceptPage";
import { ProjectInviteAcceptPage } from "./pages/ProjectInviteAcceptPage";

function App() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  // "/" always manages its own full-page chrome (LandingPage for guests,
  // AppShell for members) — the shared public Navbar/sky wrapper below is
  // only for the smaller public utility pages (login, oauth, invites).
  // "/welcome" always shows the marketing LandingPage regardless of login
  // state, so the logo can send logged-in users back to the very first screen.
  const isSelfContained =
    location.pathname === "/" ||
    location.pathname === "/welcome" ||
    (isAuthenticated && (location.pathname.startsWith("/projects") || location.pathname.startsWith("/teams")));

  const routes = (
    <Routes>
      <Route path="/" element={isAuthenticated ? <AppShell /> : <LandingPage />}>
        <Route index element={<DashboardPage />} />
      </Route>
      <Route path="/welcome" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
      <Route path="/invite/:token" element={<InviteAcceptPage />} />
      <Route path="/project-invite/:token" element={<ProjectInviteAcceptPage />} />
      <Route element={<AppShell />}>
        <Route path="/projects/:projectId" element={<ProjectPage />} />
        <Route path="/teams/:teamId" element={<TeamPage />} />
      </Route>
    </Routes>
  );

  if (!isSelfContained) {
    return (
      <div className="public-shell">
        <SkyBackground />
        <div className="public-shell-inner">
          <Navbar />
          {routes}
        </div>
      </div>
    );
  }

  return routes;
}

export default App;
