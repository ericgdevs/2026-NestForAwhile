import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Scan } from './Scan'

test('shows a friendly safety result for a manual code', async () => {
  const user = userEvent.setup()
  render(<Scan />)
  await user.type(screen.getByLabelText('Product code'), '012345')
  await user.click(screen.getByRole('button', { name: 'Check code' }))
  expect(screen.getByRole('heading', { name: 'Brown rice' })).toBeInTheDocument()
  expect(screen.getByText('Good to go')).toBeInTheDocument()
})

test('explains when a product code is unknown', async () => {
  const user = userEvent.setup()
  render(<Scan />)
  await user.type(screen.getByLabelText('Product code'), '000000')
  await user.click(screen.getByRole('button', { name: 'Check code' }))
  expect(screen.getByRole('alert')).toHaveTextContent('couldn’t find')
})
