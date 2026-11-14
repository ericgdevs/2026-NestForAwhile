import type { MockUser } from './auth'

export const rolePaths: Record<MockUser['role'], string[]> = {
  Client: ['/', '/home', '/profile', '/scan', '/cart', '/recipes'],
  Volunteer: ['/checkout'],
  'Warehouse Staff': ['/inventory', '/audit'],
  'Warehouse Manager': ['/inventory', '/audit', '/checkout'],
  Director: ['/inventory'],
}

export function canAccessPath(role: MockUser['role'], path: string) {
  return rolePaths[role].some((allowedPath) => path === allowedPath || (allowedPath !== '/' && path.startsWith(`${allowedPath}/`)))
}
