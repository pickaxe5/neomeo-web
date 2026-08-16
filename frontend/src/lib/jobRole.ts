import type { JobRole } from "../types/api";

export const JOB_ROLE_LABELS: Record<JobRole, string> = {
  frontend: "프론트엔드",
  backend: "백엔드",
  ai: "AI",
  design: "디자인",
  planning: "기획",
};

export const JOB_ROLE_OPTIONS: JobRole[] = ["frontend", "backend", "ai", "design", "planning"];
