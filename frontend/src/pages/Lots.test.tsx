import { render, screen } from '@testing-library/react'
import { Lots } from './Lots'

test('highlights expiring inventory lots', () => {
  render(<Lots />)
  expect(screen.getByRole('alert')).toHaveTextContent('2 lots expire soon')
  expect(screen.getAllByText('Expiring soon')).toHaveLength(2)
})
