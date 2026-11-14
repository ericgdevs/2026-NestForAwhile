import { EmptyState } from '../components/States'

export function Placeholder({ title, message }: { title: string; message: string }) {
  return <div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Coming up next</p><h1 className="mt-2 text-3xl font-bold text-sage-950">{title}</h1><div className="mt-8"><EmptyState title="This space is ready for your visit" message={message} /></div></div>
}
