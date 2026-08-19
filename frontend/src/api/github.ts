import { apiRequest } from "./client";
import type { GithubConnectResult, GithubRepoOut, GithubRepoStatusOut } from "../types/api";

export function connectGithub(projectId: string, repoFullName: string) {
  return apiRequest<GithubConnectResult>(`/projects/${projectId}/github/connect`, {
    method: "POST",
    body: { repo_full_name: repoFullName },
  });
}

// 프로젝트당 레포를 여러 개 연결할 수 있어 연결된 레포 목록을 반환한다.
export function fetchGithubStatus(projectId: string) {
  return apiRequest<GithubRepoStatusOut[]>(`/projects/${projectId}/github/status`);
}

export function disconnectGithub(projectId: string, repoId: string) {
  return apiRequest<void>(`/projects/${projectId}/github/repos/${repoId}`, { method: "DELETE" });
}

export function fetchMyGithubRepos() {
  return apiRequest<GithubRepoOut[]>("/me/github/repos");
}
