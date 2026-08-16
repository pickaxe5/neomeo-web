import type { TimelineCardOut } from "../types/api";
import { useLanguage } from "../i18n/LanguageContext";

function formatRange(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  return `${fmt(s)} → ${fmt(e)}`;
}

export function TimelineCard({ card }: { card: TimelineCardOut }) {
  const { t } = useLanguage();

  return (
    <div className="card timeline-card">
      <div className="row">
        <span className="badge">
          {card.trigger_type === "auto" ? t("timeline.autoClosed") : t("timeline.manualClosed")}
        </span>
        {card.status === "no_change" && <span className="badge muted">{t("timeline.noChange")}</span>}
      </div>
      <div className="meta">{formatRange(card.range_start, card.range_end)}</div>
      {card.content === null ? (
        <p className="content" style={{ opacity: 0.6 }}>
          {t("timeline.cardGenerating")}
        </p>
      ) : (
        <p className="content">{card.content}</p>
      )}
      {card.source_event_urls.length > 0 && (
        <div className="sources">
          {card.source_event_urls.map((url) => (
            <a key={url} href={url} target="_blank" rel="noreferrer">
              {url}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
