import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Sidebar() {
  const { user, logout } = useAuth();
  const displayName = user?.name ?? user?.github_handle ?? user?.email ?? "사용자";

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="mark">너</span>
        neomeo
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M2 8.5 8 3l6 5.5M4 7v6h8V7"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          대시보드
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="avatar">{displayName.slice(0, 1)}</span>
          <span className="sidebar-user-name">{displayName}</span>
        </div>
        <button onClick={logout}>로그아웃</button>
      </div>
    </aside>
  );
}
