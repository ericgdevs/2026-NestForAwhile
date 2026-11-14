import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CartProvider, useCart } from '../lib/cart'
import { Recipes } from './Recipes'

function SeededRecipes() {
  const { addItem } = useCart()
  return <><button onClick={() => addItem({ productId: 1, name: 'Brown rice' })}>Seed recipe</button><Recipes /></>
}

test('shows fallback recipes with ingredient locations', async () => {
  const user = userEvent.setup()
  render(<CartProvider><SeededRecipes /></CartProvider>)
  await user.click(screen.getByRole('button', { name: 'Seed recipe' }))
  expect(screen.getByRole('heading', { name: 'Comforting black bean bowls' })).toBeInTheDocument()
  expect(screen.getByText(/fallback recipe/i)).toBeInTheDocument()
  expect(screen.getByText(/Aisle 2/)).toBeInTheDocument()
})
