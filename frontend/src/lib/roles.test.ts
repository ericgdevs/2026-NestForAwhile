import { canAccessPath } from './roles'

test('limits client access to client screens', () => {
  expect(canAccessPath('Client', '/cart')).toBe(true)
  expect(canAccessPath('Client', '/checkout')).toBe(false)
  expect(canAccessPath('Volunteer', '/checkout')).toBe(true)
})
