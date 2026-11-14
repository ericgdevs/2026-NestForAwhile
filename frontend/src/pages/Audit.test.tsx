import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Audit } from './Audit'

test('calculates and confirms an inventory variance', async () => {
  const user = userEvent.setup()
  render(<Audit />)
  await user.type(screen.getByLabelText('Product code'), '012345')
  await user.click(screen.getByRole('button', { name: 'Check code' }))
  await user.type(screen.getByLabelText('Actual count'), '6')
  expect(screen.getByText('Variance: -2')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Confirm count' }))
  expect(screen.getByRole('status')).toHaveTextContent('Audit saved')
})
