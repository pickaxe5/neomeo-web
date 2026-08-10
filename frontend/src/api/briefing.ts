import { apiRequest } from "./client";
import type { BriefingOut } from "../types/api";

export function fetchBriefing(projectId: string) {
  return apiRequest<BriefingOut>(`/projects/${projectId}/briefing`);
}
