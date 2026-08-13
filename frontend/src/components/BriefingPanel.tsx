import type { BriefingItem, BriefingOut } from "../types/api";

function BriefingItemRow({ item }: { item: BriefingItem }) {
  return (
    <div className="briefing-item">
      <a href={item.url} target="_blank" rel="noreferrer">
        {item.title}
      </a>
      <p className="reason">{item.reason}</p>
    </div>
  );
}

export function BriefingPanel({ briefing }: { briefing: BriefingOut }) {
  const isEmpty =
    briefing.needs_my_response.length === 0 &&
    briefing.affects_my_work.length === 0 &&
    !briefing.team_progress_summary;

  if (isEmpty) {
    return (
      <div className="empty-state">
        <p>아직 브리핑할 항목이 없습니다.</p>
        <p style={{ fontSize: 13, opacity: 0.7 }}>
          AI 브리핑 생성 기능은 준비 중입니다. GitHub 활동이 쌓이면 이곳에 표시됩니다.
        </p>
      </div>
    );
  }

  return (
    <div className="stack">
      {briefing.team_progress_summary && (
        <div className="card">
          <h3>팀 진행 요약</h3>
          <p>{briefing.team_progress_summary}</p>
        </div>
      )}
      {briefing.needs_my_response.length > 0 && (
        <div className="card">
          <h3>내가 답해야 할 질문</h3>
          <div className="briefing-list">
            {briefing.needs_my_response.map((item) => (
              <BriefingItemRow key={item.url} item={item} />
            ))}
          </div>
        </div>
      )}
      {briefing.affects_my_work.length > 0 && (
        <div className="card">
          <h3>내 작업에 영향을 주는 변경</h3>
          <div className="briefing-list">
            {briefing.affects_my_work.map((item) => (
              <BriefingItemRow key={item.url} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
