import { apiRequest } from "./client";
import type { MyTeamOut, MyProjectOut } from "../types/api";

export function fetchMyTeams() {
  return apiRequest<MyTeamOut[]>("/me/teams");
}

export function fetchMyProjects() {
  return apiRequest<MyProjectOut[]>("/me/projects");
}
