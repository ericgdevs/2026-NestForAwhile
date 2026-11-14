import { beforeEach, afterEach, expect, test, vi } from 'vitest'
import { api } from './client'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

test('includes cookies and returns typed login data', async () => {
  vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ role: 'Client' }), { status: 200 }))
  await expect(api.login({ email: 'demo@example.test', password: 'welcome' })).resolves.toEqual({ role: 'Client' })
  expect(fetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({ credentials: 'include', method: 'POST' }))
})

test('surfaces API error details', async () => {
  vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ detail: 'Not active' }), { status: 403 }))
  await expect(api.me()).rejects.toThrow('Not active')
})
