import type { components } from "./generated";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? "/api" : "");

type Json = Record<string, unknown> | unknown[];

async function send<T>(path: string, init?: RequestInit): Promise<T> {
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

// Screens that ask for the same data at the same moment (household, list) share one request.
const inFlight = new Map<string, Promise<unknown>>();

function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const shareable = (!init?.method || init.method === "GET") && !init?.signal;
  if (!shareable) return send<T>(path, init);
  const pending = inFlight.get(path) ?? send<T>(path, init).finally(() => inFlight.delete(path));
  inFlight.set(path, pending);
  return pending as Promise<T>;
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

type SafetyStatus = components["schemas"]["SafetyStatus"];
export type Location = { aisle: string; shelf: string; bin: string };
/** A household member a product isn't safe for, by nickname (never a real name). */
export type NotFor = { nickname: string; reason: string };
/** Household label fields the rules engine adds to products. */
export type HouseholdLabel = { status: SafetyStatus; not_for?: NotFor[]; allergy_match?: boolean };

export type Member = {
  nickname: string;
  age: number | null;
  restrictions: string[];
  allergies: string[];
  conditions?: string[]; // ICD-10 codes, only ever returned to the client themselves
};
export type MemberInput = Partial<Omit<Member, "nickname">> & { nickname?: string; conditions?: string[] };

export type Me = {
  role?: components["schemas"]["Role"];
  client_id?: number;
  Household_Size?: number;
  Client_Enrollment_Status?: "Active" | "Inactive" | "Pending";
  profile?: { restrictions: string[]; allergies: string[]; preferences: string[] };
  members?: Member[];
};

export function getMe(): Promise<Me> {
  return apiRequest("/me");
}

export type SignupRequest = { email: string; password: string; name: string; members: MemberInput[] };

export function signup(payload: SignupRequest): Promise<components["schemas"]["LoginResult"]> {
  return apiRequest("/auth/signup", { method: "POST", body: payload });
}

export function getHousehold(): Promise<{ members: Member[] }> {
  return apiRequest("/me/household");
}

export function saveHousehold(members: MemberInput[]): Promise<{ members: Member[] }> {
  return apiRequest("/me/household", { method: "PUT", body: { members } });
}

export type VisitState =
  | { status: "awaiting_approval" | "inactive" | "none" }
  | { status: "shopping"; Shopping_Session_Token: string }
  | { status: "queued"; queue_status: "waiting" | "ready"; position: number | null; message: string }
  | { status: "complete"; receipt: { checkout_id: number; total_lb: number; completed_at: string } };

export function getVisit(): Promise<VisitState> {
  return apiRequest("/me/visit");
}

/** Start or resume a visit while signed in (no password); joins the queue if the floor is full. */
export function checkIn(): Promise<VisitState> {
  return apiRequest("/me/check-in", { method: "POST" });
}

export function getMySession(): Promise<{ Shopping_Session_Token: string; client_id: number }> {
  return apiRequest("/me/session");
}

export type PendingClient = { client_id: number; name: string; Household_Size: number; created_at: string };

export function getPendingClients(): Promise<PendingClient[]> {
  return apiRequest("/clients/pending");
}

export function approveClient(clientId: number) {
  return apiRequest(`/clients/${clientId}/approve`, { method: "POST" });
}

export function getCapacity(): Promise<components["schemas"]["Capacity"]> {
  return apiRequest("/capacity");
}

export type Recommendation = HouseholdLabel & {
  product_id: number;
  name: string;
  quantity: number;
  rationale: string;
  aisle: string;
  shelf: string;
  bin: string;
};

export function getRecommendations(): Promise<Recommendation[]> {
  return apiRequest("/recommendations");
}

export type Swap = HouseholdLabel & Location & { product_id: number; name: string };

export type ScanResult = HouseholdLabel & {
  product_id: number | null;
  sku: string;
  barcode: string;
  name: string;
  image_url: string | null;
  sodium_mg: number | null;
  sugar_g: number | null;
  sat_fat_g: number | null;
  potassium_mg: number | null;
  calories?: number | null;
  carbs_g?: number | null;
  serving_size_g?: number | null;
  total_fat_g?: number | null;
  trans_fat_g?: number | null;
  cholesterol_mg?: number | null;
  fiber_g?: number | null;
  added_sugar_g?: number | null;
  protein_g?: number | null;
  vitamin_d_mcg?: number | null;
  calcium_mg?: number | null;
  iron_mg?: number | null;
  explanation: string;
  swaps?: Swap[];
};

export function scanProduct(code: string): Promise<ScanResult> {
  return apiRequest(`/products/scan/${encodeURIComponent(code)}`);
}

export type CartItem = {
  product_id: number;
  name: string;
  quantity: number;
  from_recommendation: boolean;
  // Sent by api/client-flow (B3/cart nutrition); optional until that branch merges.
  sku?: string;
  status?: SafetyStatus;
  not_for?: NotFor[];
  allergy_match?: boolean;
  explanation?: string;
  sodium_mg?: number | null;
  sugar_g?: number | null;
  sat_fat_g?: number | null;
  potassium_mg?: number | null;
  calories?: number | null;
  carbs_g?: number | null;
  serving_size_g?: number | null;
  total_fat_g?: number | null;
  trans_fat_g?: number | null;
  cholesterol_mg?: number | null;
  fiber_g?: number | null;
  added_sugar_g?: number | null;
  protein_g?: number | null;
  vitamin_d_mcg?: number | null;
  calcium_mg?: number | null;
  iron_mg?: number | null;
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
  id?: number; // set on saved recipes
  title: string;
  cuisine?: string | null;
  ingredients: {
    name: string;
    product_id: number | null;
    in_cart_or_stock?: boolean;
    location?: Location | null;
  }[];
  steps: string[];
};

export function getRecipes(
  options: { scanned_product_id?: number; cuisine?: string } = {},
): Promise<{ recipes: Recipe[]; used_fallback: boolean }> {
  return apiRequest("/recipes", { method: "POST", body: options });
}

export function getSavedRecipes(): Promise<Recipe[]> {
  return apiRequest("/me/recipes");
}

/** What a recipe's "Save" or "Add to list" did to the shopping list (the server works out the diff). */
export type RecipeListResult = {
  added: { name: string; location: Location | null }[];
  blocked: { name: string; not_for: NotFor[]; swaps: Swap[] }[];
  in_cart: number;
  already_on_list: number;
};

/** Saving a recipe also puts its missing ingredients on the list; `skipProductId` is the item just scanned. */
export async function saveRecipe(recipe: Recipe, skipProductId?: number | null): Promise<RecipeListResult> {
  const { title, cuisine, ingredients, steps } = recipe;
  const saved = await apiRequest<{ list: RecipeListResult }>("/me/recipes", {
    method: "POST",
    body: { title, cuisine, ingredients, steps, skip_product_id: skipProductId ?? null },
  });
  return saved.list;
}

export function deleteSavedRecipe(id: number) {
  return apiRequest(`/me/recipes/${id}`, { method: "DELETE" });
}

export type ListLine = {
  id: number;
  text: string;
  product_id: number | null;
  name: string;
  source: "you" | "recipe";
  recipes: Recipe[]; // every recipe this one line is for
  ticked: boolean;
  in_stock: boolean;
  location: Location | null;
  status?: SafetyStatus;
  not_for?: NotFor[];
};

export function getShoppingList(): Promise<{ items: ListLine[] }> {
  return apiRequest("/shopping-list");
}

export function addToShoppingList(items: { text: string; product_id?: number | null; note?: boolean }[], recipe?: Recipe) {
  return apiRequest<{ items: ListLine[] }>("/shopping-list", { method: "POST", body: { items, recipe } });
}

export function tickListLine(id: number, ticked: boolean) {
  return apiRequest<{ items: ListLine[] }>(`/shopping-list/${id}`, { method: "PATCH", body: { ticked } });
}

/** A recipe's "Add to list": only ingredients not in the cart, not already listed and safe for everyone. */
export function addRecipeToList(recipe: Recipe, skipProductId?: number | null) {
  return apiRequest<RecipeListResult>("/shopping-list/from-recipe", {
    method: "POST",
    body: { recipe, skip_product_id: skipProductId ?? null },
  });
}

export function deleteListLine(id: number) {
  return apiRequest(`/shopping-list/${id}`, { method: "DELETE" });
}

export type ParsedLine = {
  text: string;
  product_id: number | null;
  name: string | null;
  status: SafetyStatus | null;
  location: Location | null;
  not_for?: NotFor[];
  swaps?: Swap[];
};

export function parseShoppingList(input: { text: string } | { image_base64: string; media_type: string }) {
  return apiRequest<{ lines: ParsedLine[] }>("/shopping-list/parse", { method: "POST", body: input });
}

export type CheckoutReview = {
  Shopping_Session_Token: string;
  client_id: number;
  Client_Enrollment_Status: "Active" | "Inactive" | "Pending" | null;
  items: (HouseholdLabel & { product_id: number; name: string; quantity: number; acknowledged: boolean; overridden: boolean })[];
  blocking: string[];
  needs_ack: { product_id: number; name: string; not_for: NotFor[] }[];
};

export function lookupCheckout(by: { token: string } | { client_id: number }): Promise<CheckoutReview> {
  const query = "token" in by ? `token=${encodeURIComponent(by.token)}` : `client_id=${by.client_id}`;
  return apiRequest(`/checkout/lookup?${query}`);
}

const checkoutPath = (token: string, rest: string) => `/checkout/${encodeURIComponent(token)}/${rest}`;

export function addCheckoutItem(token: string, code: string): Promise<CheckoutReview> {
  return apiRequest(checkoutPath(token, "items"), { method: "POST", body: { code } });
}

export function removeCheckoutItem(token: string, productId: number): Promise<CheckoutReview> {
  return apiRequest(checkoutPath(token, `items/${productId}`), { method: "DELETE" });
}

export function acknowledgeAllergy(token: string, productId: number): Promise<CheckoutReview> {
  return apiRequest(checkoutPath(token, "acknowledge"), { method: "POST", body: { product_id: productId } });
}

export function overrideItem(token: string, productId: number, note: string): Promise<CheckoutReview> {
  return apiRequest(checkoutPath(token, "override"), { method: "POST", body: { product_id: productId, note } });
}

export function validateCheckout(token: string): Promise<{ valid: boolean; errors: string[] }> {
  return apiRequest(`/checkout/${encodeURIComponent(token)}/validate`, { method: "POST" });
}

export function completeCheckout(token: string): Promise<{ checkout_id: number; total_lb: number }> {
  return apiRequest(`/checkout/${encodeURIComponent(token)}/complete`, { method: "POST" });
}

export function getProductLabels() {
  return apiRequest<Array<{ sku: string; name: string }>>("/products/labels");
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

// --- Reports (Warehouse Manager and Director): an anonymous visit dataset, filtered on the server ---
export type ReportFilters = Partial<
  Record<"date_from" | "date_to" | "attributed" | "donor_id" | "grant_id" | "category" | "household_min" | "household_max", string>
>;
export type ReportRow = {
  participant_id: string;
  visit_date: string;
  household_size: number;
  items: number;
  pounds: number;
  donors: string[];
  grants: string[];
};
export type ReportPreview = {
  totals: { visits: number; households: number; items: number; pounds: number };
  rows: ReportRow[];
};
export type ReportOptions = {
  donors: { id: number; label: string }[];
  grants: { id: number; label: string }[];
  categories: string[];
};

const reportQuery = (filters: ReportFilters, extra: Record<string, string> = {}) =>
  new URLSearchParams(
    Object.entries({ ...filters, ...extra }).filter((entry): entry is [string, string] => Boolean(entry[1])),
  ).toString();

export function getReportOptions(): Promise<ReportOptions> {
  return apiRequest("/reports/options");
}

export function getReportPreview(filters: ReportFilters, signal?: AbortSignal): Promise<ReportPreview> {
  return apiRequest(`/reports/preview?${reportQuery(filters)}`, { signal });
}

// A fetch (not a link) so the sign-in cookie and the dev proxy treat it as an API call, then save the blob.
async function saveFile(path: string, filename: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, credentials: "include" });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Download failed with status ${response.status}`);
  }
  const link = document.createElement("a");
  link.href = URL.createObjectURL(await response.blob());
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

export function downloadReportData(format: "csv" | "json", filters: ReportFilters) {
  return saveFile(`/reports/export?${reportQuery(filters, { format })}`, `report-data.${format}`);
}

export type ReportAudience = "donor" | "grant" | "general";
export type ReportFormat = "pdf" | "docx" | "both";

export function downloadWrittenReport(audience: ReportAudience, format: ReportFormat, filters: ReportFilters) {
  const extension = format === "both" ? "zip" : format;
  return saveFile(`/reports/written?${reportQuery(filters, { preset: audience, format })}`, `${audience}-report.${extension}`, {
    method: "POST",
  });
}
