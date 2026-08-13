import { apiRequest, API_BASE_URL } from "./client";
import type { TokenPair, UserOut } from "../types/api";

export function githubLoginUrl(): string {
  return `${API_BASE_URL}/auth/github/login`;
}

export function login(email: string, password: string) {
  return apiRequest<TokenPair>("/auth/login", {
    method: "POST",
    auth: false,
    body: { email, password },
  });
}

export function logout() {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}

export function fetchMe() {
  return apiRequest<UserOut>("/auth/me");
}
