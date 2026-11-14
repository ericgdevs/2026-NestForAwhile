import { AlertCircle, Inbox, LoaderCircle } from 'lucide-react'

export function LoadingState({ label = 'Loading your pantry...' }: { label?: string }) {
  return (
    <div role="status" className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-sage-200 bg-white/70 p-8 text-center text-sage-700">
      <LoaderCircle className="animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-sage-200 bg-white/70 p-8 text-center">
      <Inbox className="text-sage-500" aria-hidden="true" />
      <h2 className="text-lg font-semibold text-sage-950">{title}</h2>
      <p className="max-w-md text-sm text-sage-700">{message}</p>
    </div>
  )
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <div role="alert" className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
      <AlertCircle className="text-rose-700" aria-hidden="true" />
      <h2 className="text-lg font-semibold text-rose-950">We hit a small snag</h2>
      <p className="max-w-md text-sm text-rose-800">Your information is safe. Try again, or ask a volunteer for help.</p>
      {onRetry && <button className="rounded-lg bg-rose-700 px-4 py-2 text-sm font-semibold text-white" onClick={onRetry}>Try again</button>}
    </div>
  )
}
