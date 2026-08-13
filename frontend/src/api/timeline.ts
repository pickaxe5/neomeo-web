import { apiRequest } from "./client";
import type { TimelineCardOut } from "../types/api";

export function fetchTimeline(projectId: string, language: "ko" | "en" = "ko") {
  return apiRequest<TimelineCardOut[]>(`/projects/${projectId}/timeline`, {
    query: { language },
  });
}

export function triggerClosure(projectId: string, teamId: string, language: "ko" | "en" = "ko") {
  return apiRequest<TimelineCardOut>(`/projects/${projectId}/close`, {
    method: "POST",
    query: { language },
    body: { team_id: teamId },
  });
}
