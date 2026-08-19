import type { JobRole } from "../types/api";

export const JOB_ROLE_OPTIONS: JobRole[] = ["frontend", "backend", "ai", "design", "planning", "custom"];

export function jobRoleKey(role: JobRole): string {
  return `jobRole.${role}`;
}
