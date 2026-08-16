import { apiRequest } from "./client";
import type {
  TeamOut,
  TeamCreate,
  TeamUpdate,
  TeamMemberOut,
  MyAssignmentUpdate,
  InviteLinkOut,
  InviteAcceptResponse,
} from "../types/api";

export function createTeam(payload: TeamCreate) {
  return apiRequest<TeamOut>("/teams", { method: "POST", body: payload });
}

export function fetchTeam(teamId: string) {
  return apiRequest<TeamOut>(`/teams/${teamId}`);
}

export function updateTeam(teamId: string, payload: TeamUpdate) {
  return apiRequest<TeamOut>(`/teams/${teamId}`, { method: "PATCH", body: payload });
}

export function fetchTeamMembers(teamId: string) {
  return apiRequest<TeamMemberOut[]>(`/teams/${teamId}/members`);
}

export function updateMyAssignment(teamId: string, payload: MyAssignmentUpdate) {
  return apiRequest<TeamMemberOut>(`/teams/${teamId}/members/me`, {
    method: "PATCH",
    body: payload,
  });
}

export function createInviteLink(teamId: string) {
  return apiRequest<InviteLinkOut>(`/teams/${teamId}/invite-links`, { method: "POST" });
}

export function acceptInvite(token: string) {
  return apiRequest<InviteAcceptResponse>(`/invite/${token}/accept`, { method: "POST" });
}

export function deleteTeam(teamId: string) {
  return apiRequest<void>(`/teams/${teamId}`, { method: "DELETE" });
}

export function leaveTeam(teamId: string) {
  return apiRequest<void>(`/teams/${teamId}/leave`, { method: "POST" });
}
