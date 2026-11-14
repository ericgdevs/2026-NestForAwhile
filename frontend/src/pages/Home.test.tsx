import { render, screen } from '@testing-library/react'
import { Home } from './Home'

test('shows mock recommendations with rationale and status text', () => {
  render(<Home />)
  expect(screen.getByText('Brown rice')).toBeInTheDocument()
  expect(screen.getByText('A pantry staple that fits your low-sodium preferences.')).toBeInTheDocument()
  expect(screen.getAllByText('Good to go')).toHaveLength(2)
})
