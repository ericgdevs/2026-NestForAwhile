import type { MockUser } from './auth'

export const rolePaths: Record<MockUser['role'], string[]> = {
  Client: ['/', '/home', '/profile', '/scan', '/cart', '/recipes'],
  Volunteer: ['/checkout'],
  'Warehouse Staff': ['/inventory', '/audit', '/lots'],
  'Warehouse Manager': ['/inventory', '/audit', '/lots', '/checkout', '/reports'],
  Director: ['/inventory', '/lots', '/reports'],
}

export function canAccessPath(role: MockUser['role'], path: string) {
  return rolePaths[role].some((allowedPath) => path === allowedPath || (allowedPath !== '/' && path.startsWith(`${allowedPath}/`)))
}
