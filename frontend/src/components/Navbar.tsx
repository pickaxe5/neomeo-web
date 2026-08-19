import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Navbar() {
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const onLoginPage = location.pathname === "/login";

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand">
          <span className="brand-ko">너머</span>
          <span className="brand-en">NEOMEO</span>
        </Link>
        <nav>
          <LanguageSwitcher className="navbar-lang" />
          {!isAuthenticated && !onLoginPage && <Link to="/login">{t("common.login")}</Link>}
        </nav>
      </div>
    </header>
  );
}
