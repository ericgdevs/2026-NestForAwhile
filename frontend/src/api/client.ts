import type { components } from "./generated";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

type Json = Record<string, unknown> | unknown[];

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function apiRequest<T>(
  path: string,
  init?: RequestInit & { body?: Json },
): Promise<T> {
  const body =
    init?.body && typeof init.body !== "string" ? JSON.stringify(init.body) : init?.body;
  return requestJson<T>(path, { ...init, body });
}

export function login(
  credentials: components["schemas"]["LoginRequest"],
): Promise<components["schemas"]["LoginResult"]> {
  return apiRequest("/auth/login", {
    method: "POST",
    body: credentials,
  });
}

export function getMe(): Promise<components["schemas"]["Client"]> {
  return apiRequest("/me");
}

export function getCapacity(): Promise<components["schemas"]["Capacity"]> {
  return apiRequest("/capacity");
}
