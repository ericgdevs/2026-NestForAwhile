import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../lib/auth'
import { Login } from './Login'

function renderLogin() {
  return render(<MemoryRouter><AuthProvider><Login /></AuthProvider></MemoryRouter>)
}

test('shows a friendly message for invalid credentials', async () => {
  const user = userEvent.setup()
  renderLogin()
  await user.type(screen.getByLabelText('Email'), 'wrong@example.test')
  await user.type(screen.getByLabelText('Password'), 'nope')
  await user.click(screen.getByRole('button', { name: 'Sign in' }))
  expect(screen.getByRole('alert')).toHaveTextContent('did not match')
})

test('explains when enrollment is not active', async () => {
  const user = userEvent.setup()
  renderLogin()
  await user.type(screen.getByLabelText('Email'), 'pending@example.test')
  await user.type(screen.getByLabelText('Password'), 'welcome')
  await user.click(screen.getByRole('button', { name: 'Sign in' }))
  expect(screen.getByRole('alert')).toHaveTextContent('enrollment is not active')
})
