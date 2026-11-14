import { render, screen } from '@testing-library/react'
import { StatusBadge } from './StatusBadge'

test('communicates status with text and icon', () => {
  render(<StatusBadge status="yellow" />)
  expect(screen.getByText('Review needed')).toBeInTheDocument()
  expect(screen.getByText('Review needed').closest('span')).toHaveClass('text-amber-800')
})
