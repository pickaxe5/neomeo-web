import { Route, Routes } from "react-router-dom";
import "./App.css";
import { Navbar } from "./components/Navbar";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { TeamPage } from "./pages/TeamPage";
import { InviteAcceptPage } from "./pages/InviteAcceptPage";

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
        <Route path="/invite/:token" element={<InviteAcceptPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:projectId"
          element={
            <ProtectedRoute>
              <ProjectPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teams/:teamId"
          element={
            <ProtectedRoute>
              <TeamPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}

export default App;
