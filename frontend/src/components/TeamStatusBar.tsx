import { useEffect, useState } from "react";
import { useLanguage } from "../i18n/LanguageContext";

type StatusTeam = {
  id: string;
  name: string;
  country: string | null;
  timezone: string;
  work_start: string;
  work_end: string;
};

function localTimeParts(timezone: string, now: Date): { hm: string; display: string } {
  try {
    const hm = new Intl.DateTimeFormat("en-GB", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(now);
    return { hm, display: hm };
  } catch {
    return { hm: "", display: "--:--" };
  }
}

function isWorking(hm: string, workStart: string, workEnd: string): boolean {
  if (!hm) return false;
  const start = workStart.slice(0, 5);
  const end = workEnd.slice(0, 5);
  if (start <= end) {
    return hm >= start && hm < end;
  }
  // overnight shift (e.g. 22:00–06:00)
  return hm >= start || hm < end;
}

export function TeamStatusBar({ teams }: { teams: StatusTeam[] }) {
  const { t } = useLanguage();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(id);
  }, []);

  if (teams.length === 0) return null;

  return (
    <div className="team-status-bar">
      {teams.map((team) => {
        const { hm, display } = localTimeParts(team.timezone, now);
        const working = isWorking(hm, team.work_start, team.work_end);
        return (
          <div key={team.id} className="team-status-chip">
            <span className="name">
              {team.name}
              {team.country && <span className="country"> · {team.country}</span>}
            </span>
            <span className="time">{display}</span>
            <span className={`badge ${working ? "ok" : "muted"}`}>
              {working ? t("timeline.working") : t("timeline.off")}
            </span>
          </div>
        );
      })}
    </div>
  );
}
