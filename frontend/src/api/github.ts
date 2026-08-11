import { apiRequest } from "./client";
import type { GithubConnectResult, GithubRepoOut, GithubStatusOut } from "../types/api";

export function connectGithub(projectId: string, repoFullName: string) {
  return apiRequest<GithubConnectResult>(`/projects/${projectId}/github/connect`, {
    method: "POST",
    body: { repo_full_name: repoFullName },
  });
}

export function fetchGithubStatus(projectId: string) {
  return apiRequest<GithubStatusOut>(`/projects/${projectId}/github/status`);
}

/**
 * NOT YET IMPLEMENTED on the backend — 404s today.
 * Requested contract: docs/frontend-to-backend-requests.md
 */
export function fetchMyGithubRepos() {
  return apiRequest<GithubRepoOut[]>("/me/github/repos");
}
