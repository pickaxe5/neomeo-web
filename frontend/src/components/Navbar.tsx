import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const displayName = user?.name ?? user?.github_handle ?? user?.email ?? "사용자";

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="mark">너</span>
        neomeo
      </Link>
      <nav>
        {isAuthenticated ? (
          <>
            <Link to="/">대시보드</Link>
            <span className="user">
              <span className="avatar">{displayName.slice(0, 1)}</span>
              {displayName}
              <button onClick={logout}>로그아웃</button>
            </span>
          </>
        ) : (
          <Link to="/login">로그인</Link>
        )}
      </nav>
    </header>
  );
}
