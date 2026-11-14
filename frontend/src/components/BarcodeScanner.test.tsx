import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BarcodeScanner } from './BarcodeScanner'

test('always supports manual SKU entry', async () => {
  const user = userEvent.setup()
  const onDetected = vi.fn()
  render(<BarcodeScanner onDetected={onDetected} />)
  await user.type(screen.getByLabelText('Product code'), '  012345  ')
  await user.click(screen.getByRole('button', { name: 'Check code' }))
  expect(onDetected).toHaveBeenCalledWith('012345')
})
