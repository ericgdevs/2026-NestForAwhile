import { ArrowRight, CalendarHeart, Sparkles } from 'lucide-react'
import { StatusBadge } from '../components/StatusBadge'
import { EmptyState } from '../components/States'

export function Home() {
  return (
    <div>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Tuesday, November 14</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-sage-950 sm:text-4xl">A gentler grocery trip starts here.</h1><p className="mt-3 max-w-2xl text-sage-700">We picked a few items that fit your preferences and what’s available today.</p></div><StatusBadge status="green" label="Your session is active" /></div>
      <div className="mt-8 grid gap-5 md:grid-cols-3">
        <section className="rounded-3xl bg-sage-700 p-6 text-white md:col-span-2"><Sparkles className="text-sage-200" /><h2 className="mt-8 text-2xl font-bold">Your next best pick</h2><p className="mt-2 max-w-md text-sage-100">Brown rice, canned black beans, and tomatoes are all in stock and work well together.</p><button className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-bold text-sage-800">View recipe <ArrowRight size={17} /></button></section>
        <section className="rounded-3xl border border-sage-200 bg-white p-6"><CalendarHeart className="text-sage-700" /><h2 className="mt-5 text-lg font-bold text-sage-950">Your visit</h2><p className="mt-2 text-sm text-sage-700">You have plenty of time today. Take it at your own pace.</p><div className="mt-6 border-t border-sage-100 pt-4 text-sm text-sage-700"><strong className="block text-sage-950">12 items</strong>recommended for your household</div></section>
      </div>
      <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-bold text-sage-950">Recommended for you</h2><button className="text-sm font-semibold text-sage-700">See all</button></div><EmptyState title="Your recommendations are getting ready" message="Once your shopping session is fully synced, your personalized items will appear here." /></section>
    </div>
  )
}
