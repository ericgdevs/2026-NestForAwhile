import { CheckCircle2, CircleAlert, CircleX } from 'lucide-react'
import { cn } from '../lib/utils'

type Status = 'green' | 'yellow' | 'red'

const statusDetails = {
  green: { label: 'Good to go', icon: CheckCircle2, styles: 'bg-emerald-50 text-emerald-800 ring-emerald-200' },
  yellow: { label: 'Review needed', icon: CircleAlert, styles: 'bg-amber-50 text-amber-800 ring-amber-200' },
  red: { label: 'Not available', icon: CircleX, styles: 'bg-rose-50 text-rose-800 ring-rose-200' },
} satisfies Record<Status, { label: string; icon: typeof CheckCircle2; styles: string }>

export function StatusBadge({ status, label }: { status: Status; label?: string }) {
  const details = statusDetails[status]
  const Icon = details.icon
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ring-1', details.styles)}>
      <Icon aria-hidden="true" size={16} />
      {label ?? details.label}
    </span>
  )
}
