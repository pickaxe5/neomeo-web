import { apiRequest } from "./client";
import type { BriefingOut } from "../types/api";

export function fetchBriefing(projectId: string) {
  return apiRequest<BriefingOut>(`/projects/${projectId}/briefing`);
}

export function resolveUnansweredItem(projectId: string, itemId: string, resolved: boolean) {
  return apiRequest<void>(`/projects/${projectId}/unanswered-items/${itemId}/resolve`, {
    method: "PATCH",
    body: { resolved },
  });
}
