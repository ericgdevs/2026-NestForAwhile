import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CartProvider, useCart } from '../lib/cart'
import { Checkout } from './Checkout'

function SeededCheckout() {
  const { addItem } = useCart()
  return <><button onClick={() => addItem({ productId: 1, name: 'Brown rice' })}>Seed checkout</button><Checkout /></>
}

test('completes a clean cart with a session token', async () => {
  const user = userEvent.setup()
  render(<CartProvider><SeededCheckout /></CartProvider>)
  await user.click(screen.getByRole('button', { name: 'Seed checkout' }))
  await user.type(screen.getByLabelText('Shopping_Session_Token'), 'session-demo')
  await user.click(screen.getByRole('button', { name: 'Complete checkout' }))
  expect(screen.getByRole('heading', { name: 'Checkout complete' })).toBeInTheDocument()
})
