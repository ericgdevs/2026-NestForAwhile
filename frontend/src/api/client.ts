import type { components, paths } from './generated/schema'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

type JsonResponse = { content: { 'application/json': unknown } }
type SuccessResponse<Path extends keyof paths, Method extends keyof paths[Path]> =
  paths[Path][Method] extends { responses: infer Responses }
    ? Responses extends { 200: infer Response }
      ? Response extends JsonResponse
        ? Response['content']['application/json']
        : never
      : Responses extends { 204: unknown }
        ? void
        : never
    : never

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })

  if (!response.ok) {
    const error = (await response.json().catch(() => null)) as components['schemas']['Error'] | null
    throw new Error(error?.detail ?? `Request failed with status ${response.status}`)
  }

  return response.status === 204 ? (undefined as T) : (await response.json() as T)
}

export const api = {
  login: (body: components['schemas']['LoginRequest']) =>
    request<SuccessResponse<'/auth/login', 'post'>>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  me: () => request<SuccessResponse<'/me', 'get'>>('/me'),
  recommendations: () => request<SuccessResponse<'/recommendations', 'get'>>('/recommendations'),
  cart: () => request<SuccessResponse<'/cart', 'get'>>('/cart'),
}
