import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider, ProtectedRoute, useAuth } from './auth'

function TestApp() {
  return <MemoryRouter initialEntries={['/private']}><AuthProvider><Routes><Route element={<ProtectedRoute />}><Route path="/private" element={<p>Private</p>} /></Route><Route path="/login" element={<p>Login</p>} /></Routes></AuthProvider></MemoryRouter>
}

test('redirects signed-out visitors to login', () => {
  render(<TestApp />)
  expect(screen.getByText('Login')).toBeInTheDocument()
})

test('accepts the demo credentials', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><AuthProvider><TestCredentials /></AuthProvider></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: 'Sign in' }))
  expect(screen.getByText('Signed in')).toBeInTheDocument()
})

function TestCredentials() {
  const { signIn } = useAuth()
  const [signedIn, setSignedIn] = useState(false)
  return <button onClick={() => setSignedIn(signIn('demo@example.test', 'welcome').ok)}>{signedIn ? 'Signed in' : 'Sign in'}</button>
}
