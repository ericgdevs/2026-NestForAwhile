import type { components } from "./generated";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

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

export type Recommendation = {
  product_id: number;
  name: string;
  quantity: number;
  status: components["schemas"]["SafetyStatus"];
  rationale: string;
  aisle: string;
  shelf: string;
  bin: string;
};

export function getRecommendations(): Promise<Recommendation[]> {
  return apiRequest("/recommendations");
}

export type ScanResult = {
  product_id: number | null;
  sku: string;
  barcode: string;
  name: string;
  image_url: string | null;
  sodium_mg: number | null;
  sugar_g: number | null;
  sat_fat_g: number | null;
  potassium_mg: number | null;
  status: components["schemas"]["SafetyStatus"];
  explanation: string;
};

export function scanProduct(code: string): Promise<ScanResult> {
  return apiRequest(`/products/scan/${encodeURIComponent(code)}`);
}
