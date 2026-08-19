import { useState } from "react";
import type { BriefingItem, BriefingOut, ParticipatingTeamOut } from "../types/api";
import { resolveUnansweredItem } from "../api/briefing";
import { errorMessage } from "./ErrorBanner";
import { formatRange } from "./TimelineCard";
import { useLanguage } from "../i18n/LanguageContext";

function NeedsResponseRow({
  item,
  projectId,
  resolved,
  onToggled,
}: {
  item: BriefingItem;
  projectId: string;
  resolved: boolean;
  onToggled: (id: string, resolved: boolean) => void;
}) {
  const { t } = useLanguage();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggle() {
    if (!item.id) return;
    setBusy(true);
    setError(null);
    try {
      await resolveUnansweredItem(projectId, item.id, !resolved);
      onToggled(item.id, !resolved);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`briefing-item${resolved ? " resolved" : ""}`}>
      <div className="row">
        <a href={item.url} target="_blank" rel="noreferrer">
          {item.title}
        </a>
        <button onClick={toggle} disabled={busy} style={{ flexShrink: 0 }}>
          {resolved ? t("briefing.undoDone") : t("briefing.markDone")}
        </button>
      </div>
      <p className="reason">{item.reason}</p>
      {error && <p className="reason" style={{ color: "var(--danger)" }}>{error}</p>}
    </div>
  );
}

function InfoRow({ item }: { item: BriefingItem }) {
  return (
    <div className="briefing-item">
      <a href={item.url} target="_blank" rel="noreferrer">
        {item.title}
      </a>
      <p className="reason">{item.reason}</p>
    </div>
  );
}

export function BriefingPanel({
  briefing,
  projectId,
  teams,
}: {
  briefing: BriefingOut;
  projectId: string;
  teams: ParticipatingTeamOut[];
}) {
  const { t } = useLanguage();
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());
  const teamName = (teamId: string) => teams.find((team) => team.id === teamId)?.name ?? teamId;

  function handleToggled(id: string, resolved: boolean) {
    setResolvedIds((prev) => {
      const next = new Set(prev);
      if (resolved) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  const isEmpty =
    briefing.needs_my_response.length === 0 &&
    briefing.affects_my_work.length === 0 &&
    briefing.team_progress_summary.length === 0;

  if (isEmpty) {
    return (
      <div className="empty-state">
        <p>{t("briefing.empty")}</p>
      </div>
    );
  }

  const sortedNeedsResponse = [...briefing.needs_my_response].sort((a, b) => {
    const aResolved = a.id ? resolvedIds.has(a.id) : false;
    const bResolved = b.id ? resolvedIds.has(b.id) : false;
    return Number(aResolved) - Number(bResolved);
  });

  return (
    <div className="stack">
      {briefing.needs_my_response.length > 0 && (
        <div className="card">
          <h3>{t("briefing.needsResponse")}</h3>
          <div className="briefing-list">
            {sortedNeedsResponse.map((item) => (
              <NeedsResponseRow
                key={item.id ?? item.url}
                item={item}
                projectId={projectId}
                resolved={item.id ? resolvedIds.has(item.id) : false}
                onToggled={handleToggled}
              />
            ))}
          </div>
        </div>
      )}
      {briefing.affects_my_work.length > 0 && (
        <div className="card">
          <h3>{t("briefing.affectsWork")}</h3>
          <div className="briefing-list">
            {briefing.affects_my_work.map((item) => (
              <InfoRow key={item.url} item={item} />
            ))}
          </div>
        </div>
      )}
      {briefing.team_progress_summary.length > 0 && (
        <div className="card">
          <h3>{t("briefing.teamProgress")}</h3>
          <div className="briefing-list">
            {briefing.team_progress_summary.map((card, i) => (
              <div key={`${card.team_id}-${card.range_end}-${i}`} className="briefing-item">
                <div className="row">
                  <strong>{teamName(card.team_id)}</strong>
                  <span className="reason">{formatRange(card.range_start, card.range_end)}</span>
                </div>
                <p className="reason" style={card.content ? undefined : { opacity: 0.6 }}>
                  {card.content ?? t("timeline.cardGenerating")}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
