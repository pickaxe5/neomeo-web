import { useLanguage } from "../i18n/LanguageContext";
import type { Lang } from "../i18n/dictionary";

export function LanguageSwitcher({ className }: { className?: string }) {
  const { lang, setLang, t } = useLanguage();

  return (
    <select
      className={className}
      aria-label={t("lang.switcherLabel")}
      value={lang}
      onChange={(e) => setLang(e.target.value as Lang)}
    >
      <option value="ko">한국어</option>
      <option value="en">English</option>
    </select>
  );
}
