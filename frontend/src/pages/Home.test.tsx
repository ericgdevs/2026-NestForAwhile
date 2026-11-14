import { render, screen } from '@testing-library/react'
import { Home } from './Home'
import { CartProvider } from '../lib/cart'

test('shows mock recommendations with rationale and status text', () => {
  render(<CartProvider><Home /></CartProvider>)
  expect(screen.getByText('Brown rice')).toBeInTheDocument()
  expect(screen.getByText('A pantry staple that fits your low-sodium preferences.')).toBeInTheDocument()
  expect(screen.getAllByText('Good to go')).toHaveLength(2)
})
