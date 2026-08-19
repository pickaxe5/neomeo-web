import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";
import { setApiLanguage } from "../api/client";
import { dictionary } from "./dictionary";
import type { Lang } from "./dictionary";

const LANG_STORAGE_KEY = "neomeo_lang";

function detectInitialLang(): Lang {
  const stored = localStorage.getItem(LANG_STORAGE_KEY);
  if (stored === "ko" || stored === "en") return stored;
  return navigator.language?.toLowerCase().startsWith("ko") ? "ko" : "en";
}

interface LanguageContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const initial = detectInitialLang();
    setApiLanguage(initial);
    return initial;
  });

  function setLang(next: Lang) {
    setLangState(next);
    setApiLanguage(next);
  }

  function t(key: string, vars?: Record<string, string | number>): string {
    let str = dictionary[lang][key] ?? key;
    if (vars) {
      for (const [name, value] of Object.entries(vars)) {
        str = str.replace(new RegExp(`\\{${name}\\}`, "g"), String(value));
      }
    }
    return str;
  }

  return <LanguageContext.Provider value={{ lang, setLang, t }}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
