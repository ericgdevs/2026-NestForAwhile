import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { CartProvider, useCart } from '../lib/cart'
import { Cart } from './Cart'

function SeededCart() {
  const { addItem } = useCart()
  return <><button onClick={() => addItem({ productId: 1, name: 'Brown rice' })}>Seed item</button><Cart /></>
}

test('changes quantity and removes a cart item', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><CartProvider><SeededCart /></CartProvider></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: 'Seed item' }))
  expect(screen.getByText('Brown rice')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Increase Brown rice' }))
  expect(screen.getByText('2')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Remove Brown rice' }))
  expect(screen.getByText('Your cart is waiting')).toBeInTheDocument()
})
