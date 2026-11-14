import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Profile } from './Profile'

test('allows plain-language preferences to be selected and saved', async () => {
  const user = userEvent.setup()
  render(<Profile />)
  await user.click(screen.getByLabelText('Low Sodium'))
  await user.click(screen.getByRole('button', { name: /save preferences/i }))
  expect(screen.getByRole('status')).toHaveTextContent('Saved')
  expect(screen.getByLabelText('Low Sodium')).toBeChecked()
})
