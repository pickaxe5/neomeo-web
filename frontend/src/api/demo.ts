import { apiRequest } from "./client";
import type { SeedResponse, TokenPair } from "../types/api";

export function seedDemo() {
  return apiRequest<SeedResponse>("/demo/seed", { method: "POST", auth: false });
}

export function demoLogin() {
  return apiRequest<TokenPair>("/demo/login", { method: "POST", auth: false });
}

export function simulateTime(projectId: string, simulatedNow?: string) {
  return apiRequest<{ project_id: string; simulated_now: string | null; applied: boolean }>(
    "/demo/simulate-time",
    {
      method: "POST",
      body: { project_id: projectId, simulated_now: simulatedNow },
    },
  );
}
