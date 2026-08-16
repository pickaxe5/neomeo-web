import { useState } from "react";
import type { BriefingItem, BriefingOut } from "../types/api";
import { resolveUnansweredItem } from "../api/briefing";
import { errorMessage } from "./ErrorBanner";

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
          {resolved ? "완료 취소" : "완료로 표시"}
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

export function BriefingPanel({ briefing, projectId }: { briefing: BriefingOut; projectId: string }) {
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());

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
    !briefing.team_progress_summary;

  if (isEmpty) {
    return (
      <div className="empty-state">
        <p>지금은 확인할 브리핑 항목이 없습니다.</p>
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
          <h3>내가 답해야 할 질문</h3>
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
          <h3>내 작업에 영향을 주는 변경</h3>
          <div className="briefing-list">
            {briefing.affects_my_work.map((item) => (
              <InfoRow key={item.url} item={item} />
            ))}
          </div>
        </div>
      )}
      {briefing.team_progress_summary && (
        <div className="card">
          <h3>팀 진행 요약</h3>
          <p>{briefing.team_progress_summary}</p>
        </div>
      )}
    </div>
  );
}
