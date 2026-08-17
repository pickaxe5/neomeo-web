import { apiRequest } from "./client";
import type {
  ProjectOut,
  ProjectCreate,
  ProjectDocumentOut,
  ParticipatingTeamOut,
  ProjectInviteLinkOut,
  ProjectInviteAcceptResponse,
} from "../types/api";

export function createProject(payload: ProjectCreate) {
  return apiRequest<ProjectOut>("/projects", { method: "POST", body: payload });
}

export function fetchProject(projectId: string) {
  return apiRequest<ProjectOut>(`/projects/${projectId}`);
}

export function updateProject(projectId: string, name: string) {
  return apiRequest<ProjectOut>(`/projects/${projectId}`, { method: "PATCH", body: { name } });
}

// Note: backend only exposes PUT (upsert) for the project document, no GET.
export function putProjectDocument(projectId: string, content: string) {
  return apiRequest<ProjectDocumentOut>(`/projects/${projectId}/document`, {
    method: "PUT",
    body: { content },
  });
}

export function addParticipatingTeam(projectId: string, teamId: string) {
  return apiRequest<void>(`/projects/${projectId}/teams`, {
    method: "POST",
    body: { team_id: teamId },
  });
}

export function fetchParticipatingTeams(projectId: string) {
  return apiRequest<ParticipatingTeamOut[]>(`/projects/${projectId}/teams`);
}

export function removeParticipatingTeam(projectId: string, teamId: string) {
  return apiRequest<void>(`/projects/${projectId}/teams/${teamId}`, { method: "DELETE" });
}

export function deleteProject(projectId: string) {
  return apiRequest<void>(`/projects/${projectId}`, { method: "DELETE" });
}

export function createProjectInviteLink(projectId: string) {
  return apiRequest<ProjectInviteLinkOut>(`/projects/${projectId}/invite-links`, { method: "POST" });
}

export function acceptProjectInvite(token: string, teamId: string) {
  return apiRequest<ProjectInviteAcceptResponse>(`/project-invite/${token}/accept`, {
    method: "POST",
    body: { team_id: teamId },
  });
}
