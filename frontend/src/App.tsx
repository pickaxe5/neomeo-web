import { Route, Routes, useLocation } from "react-router-dom";
import "./App.css";
import { Navbar } from "./components/Navbar";
import { AppShell } from "./components/AppShell";
import { useAuth } from "./context/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { TeamPage } from "./pages/TeamPage";
import { InviteAcceptPage } from "./pages/InviteAcceptPage";

const SHELL_PREFIXES = ["/", "/projects", "/teams"];

function App() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const isShellRoute =
    isAuthenticated &&
    SHELL_PREFIXES.some((p) => (p === "/" ? location.pathname === "/" : location.pathname.startsWith(p)));

  return (
    <>
      {!isShellRoute && <Navbar />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
        <Route path="/invite/:token" element={<InviteAcceptPage />} />
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
          <Route path="/teams/:teamId" element={<TeamPage />} />
        </Route>
      </Routes>
    </>
  );
}

export default App;
