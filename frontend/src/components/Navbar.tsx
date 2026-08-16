import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Navbar() {
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="mark">너</span>
        neomeo
      </Link>
      <nav>
        <LanguageSwitcher className="navbar-lang" />
        {!isAuthenticated && <Link to="/login">{t("common.login")}</Link>}
      </nav>
    </header>
  );
}
