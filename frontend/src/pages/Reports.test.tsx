import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Reports } from './Reports'

test('prepares an aggregate DOCX report', async () => {
  const user = userEvent.setup()
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:report')
  render(<Reports />)
  await user.selectOptions(screen.getByLabelText('Period'), 'quarter')
  await user.click(screen.getByRole('button', { name: 'Download DOCX' }))
  expect(screen.getByRole('status')).toHaveTextContent('download is ready')
})
