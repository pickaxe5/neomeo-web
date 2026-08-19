import { tokenStorage } from "./tokenStorage";
import type { TokenPair } from "../types/api";

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const LANG_STORAGE_KEY = "neomeo_lang";
let currentLang: string = localStorage.getItem(LANG_STORAGE_KEY) ?? "ko";

export function setApiLanguage(lang: string) {
  currentLang = lang;
  localStorage.setItem(LANG_STORAGE_KEY, lang);
}

export function getApiLanguage(): string {
  return currentLang;
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    })
      .then(async (res) => {
        if (!res.ok) {
          tokenStorage.clear();
          return null;
        }
        const data: TokenPair = await res.json();
        tokenStorage.setTokens(data.access_token, data.refresh_token);
        return data.access_token;
      })
      .catch(() => {
        tokenStorage.clear();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  query?: Record<string, string | number | boolean | undefined>;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function rawRequest(path: string, options: RequestOptions, accessToken: string | null): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Accept-Language": currentLang,
  };
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  return fetch(buildUrl(path, options.query), {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // response had no JSON body
    }
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : res.statusText;
    throw new ApiError(res.status, detail, body);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const auth = options.auth ?? true;
  let accessToken = auth ? tokenStorage.getAccessToken() : null;

  let res = await rawRequest(path, options, accessToken);

  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await rawRequest(path, options, newToken);
    }
  }

  return handleResponse<T>(res);
}

// For multipart file uploads — the browser must set its own
// Content-Type (with boundary), so this bypasses rawRequest's
// JSON-only header handling instead of sharing it.
async function rawUpload(path: string, formData: FormData, accessToken: string | null): Promise<Response> {
  const headers: Record<string, string> = { "Accept-Language": currentLang };
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  return fetch(buildUrl(path), { method: "POST", headers, body: formData, cache: "no-store" });
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  let accessToken = tokenStorage.getAccessToken();
  let res = await rawUpload(path, formData, accessToken);

  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await rawUpload(path, formData, newToken);
    }
  }

  return handleResponse<T>(res);
}
