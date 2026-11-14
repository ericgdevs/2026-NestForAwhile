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

export type CartItem = {
  product_id: number;
  name: string;
  quantity: number;
  from_recommendation: boolean;
};

export function getCart(): Promise<{ items: CartItem[] }> {
  return apiRequest("/cart");
}

export function saveCartItem(product_id: number, quantity: number) {
  return apiRequest<{ items: CartItem[] }>("/cart/items", {
    method: "POST",
    body: { product_id, quantity },
  });
}

export function deleteCartItem(product_id: number) {
  return apiRequest(`/cart/items/${product_id}`, { method: "DELETE" });
}

export type Recipe = {
  title: string;
  ingredients: { name: string; product_id: number | null }[];
  steps: string[];
};

export function getRecipes(): Promise<{ recipes: Recipe[]; used_fallback: boolean }> {
  return apiRequest("/recipes", { method: "POST" });
}

export function validateCheckout(token: string): Promise<{ valid: boolean; errors: string[] }> {
  return apiRequest(`/checkout/${encodeURIComponent(token)}/validate`, { method: "POST" });
}

export function completeCheckout(token: string): Promise<{ checkout_id: number; total_lb: number }> {
  return apiRequest(`/checkout/${encodeURIComponent(token)}/complete`, { method: "POST" });
}

export function getInventoryLots() {
  return apiRequest<Array<{ lot_id: number; product_id: number; quantity: number; expiration_date: string; expiring_soon: boolean }>>("/inventory/lots");
}

export function getReplenishment(sort = "priority") {
  return apiRequest<Array<{ product_id: number; name: string; quantity: number; reorder_threshold: number; aisle: string; shelf: string; bin: string; priority: number }>>(`/inventory/replenishment?sort=${sort}`);
}

export function getAnalytics() {
  return apiRequest<{ families_served: number; visits_completed: number; pounds_distributed: number; inventory_usage: number; recommendation_adoption_rate: number; waste_reduction: { expiring_soon_lots: number; pounds_saved: number } }>("/analytics");
}

export function getQueue() {
  return apiRequest<{ status: string; position: number | null; message: string }>("/queue/me");
}

export function claimQueue() {
  return apiRequest<{ Shopping_Session_Token: string }>("/queue/me", { method: "POST" });
}
