import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Navbar() {
  const { isAuthenticated } = useAuth();

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="mark">너</span>
        neomeo
      </Link>
      {!isAuthenticated && (
        <nav>
          <Link to="/login">로그인</Link>
        </nav>
      )}
    </header>
  );
}
