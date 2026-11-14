import { ArrowRight, CalendarHeart, Sparkles } from 'lucide-react'
import { StatusBadge } from '../components/StatusBadge'
import { useCart } from '../lib/cart'

const recommendations = [
  { name: 'Brown rice', quantity: '2 bags', rationale: 'A pantry staple that fits your low-sodium preferences.', status: 'green' as const },
  { name: 'Canned black beans', quantity: '4 cans', rationale: 'A flexible source of protein for your household.', status: 'green' as const },
  { name: 'Whole wheat tortillas', quantity: '1 pack', rationale: 'A practical option for quick, filling meals.', status: 'yellow' as const },
]

export function Home() {
  const { addItem } = useCart()
  return (
    <div>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Tuesday, November 14</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-sage-950 sm:text-4xl">A gentler grocery trip starts here.</h1><p className="mt-3 max-w-2xl text-sage-700">We picked a few items that fit your preferences and what’s available today.</p></div><StatusBadge status="green" label="Your session is active" /></div>
      <div className="mt-8 grid gap-5 md:grid-cols-3">
        <section className="rounded-3xl bg-sage-700 p-6 text-white md:col-span-2"><Sparkles className="text-sage-200" /><h2 className="mt-8 text-2xl font-bold">Your next best pick</h2><p className="mt-2 max-w-md text-sage-100">Brown rice, canned black beans, and tomatoes are all in stock and work well together.</p><button className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-bold text-sage-800">View recipe <ArrowRight size={17} /></button></section>
        <section className="rounded-3xl border border-sage-200 bg-white p-6"><CalendarHeart className="text-sage-700" /><h2 className="mt-5 text-lg font-bold text-sage-950">Your visit</h2><p className="mt-2 text-sm text-sage-700">You have plenty of time today. Take it at your own pace.</p><div className="mt-6 border-t border-sage-100 pt-4 text-sm text-sage-700"><strong className="block text-sage-950">12 items</strong>recommended for your household</div></section>
      </div>
      <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-bold text-sage-950">Recommended for you</h2><button className="text-sm font-semibold text-sage-700">See all</button></div><div className="grid gap-4 md:grid-cols-3">{recommendations.map((item, index) => <article key={item.name} className="rounded-2xl border border-sage-200 bg-white p-5"><div className="flex items-start justify-between gap-3"><h3 className="font-bold text-sage-950">{item.name}</h3><StatusBadge status={item.status} /></div><p className="mt-2 text-sm text-sage-700">{item.rationale}</p><p className="mt-4 text-xs font-semibold uppercase tracking-wide text-sage-500">{item.quantity} suggested</p><button className="mt-4 w-full rounded-xl border border-sage-300 px-3 py-2 text-sm font-semibold text-sage-800 hover:bg-sage-50" onClick={() => addItem({ productId: index + 1, name: item.name })}>Add to cart</button></article>)}</div></section>
    </div>
  )
}
