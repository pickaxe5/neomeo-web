import { useState } from "react";
import type { TimelineCardOut, TimelineEventType } from "../types/api";
import { useLanguage } from "../i18n/LanguageContext";

export function formatRange(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  return `${fmt(s)} → ${fmt(e)}`;
}

function eventTypeKey(type: TimelineEventType): string {
  return `timeline.eventType.${type}`;
}

export function TimelineCard({ card }: { card: TimelineCardOut }) {
  const { t } = useLanguage();
  const [showLog, setShowLog] = useState(false);
  const hasStructuredEvents = card.source_events.length > 0;

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

      {hasStructuredEvents ? (
        <>
          <button
            style={{ padding: "3px 8px", fontSize: 11.5 }}
            onClick={() => setShowLog((v) => !v)}
          >
            {showLog
              ? t("timeline.hideChangeLog")
              : t("timeline.showChangeLog", { n: card.source_events.length })}
          </button>
          {showLog && (
            <div className="list-panel" style={{ marginTop: 8 }}>
              {card.source_events.map((ev, i) => (
                <a
                  key={`${ev.url}-${i}`}
                  href={ev.url}
                  target="_blank"
                  rel="noreferrer"
                  className="list-row"
                >
                  <span className="badge muted" style={{ flexShrink: 0 }}>
                    {t(eventTypeKey(ev.type))}
                  </span>
                  <span className="list-row-main">
                    <span className="name">{ev.title}</span>
                    <span className="sub">
                      {ev.author ? `${ev.author} · ` : ""}
                      {new Date(ev.occurred_at).toLocaleString()}
                    </span>
                  </span>
                </a>
              ))}
            </div>
          )}
        </>
      ) : (
        card.source_event_urls.length > 0 && (
          <div className="sources">
            {card.source_event_urls.map((url) => (
              <a key={url} href={url} target="_blank" rel="noreferrer">
                {url}
              </a>
            ))}
          </div>
        )
      )}
    </div>
  );
}
