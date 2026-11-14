import { AlertTriangle } from 'lucide-react'

const lots = [
  { id: 1042, product: 'Brown rice', quantity: 18, expiry: 'Nov 18, 2026', expiring: true },
  { id: 1043, product: 'Canned black beans', quantity: 42, expiry: 'Dec 12, 2026', expiring: false },
  { id: 1044, product: 'Whole wheat tortillas', quantity: 9, expiry: 'Nov 20, 2026', expiring: true },
]

export function Lots() {
  const expiringCount = lots.filter((lot) => lot.expiring).length
  return <div className="mx-auto max-w-4xl"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Warehouse tools</p><h1 className="mt-2 text-3xl font-bold text-sage-950">Inventory lots</h1><p className="mt-3 text-sage-700">Keep an eye on quantities and approaching expiration dates.</p>{expiringCount > 0 && <div role="alert" className="mt-8 flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-950"><AlertTriangle className="shrink-0 text-amber-700" /><div><strong>{expiringCount} lots expire soon</strong><p className="mt-1 text-sm">Consider prioritizing these items for today’s recommendations.</p></div></div>}<div className="mt-6 overflow-hidden rounded-3xl border border-sage-200 bg-white"><div className="hidden grid-cols-[1.4fr_0.7fr_1fr_0.8fr] gap-4 border-b border-sage-100 bg-sage-50 px-5 py-3 text-xs font-bold uppercase tracking-wide text-sage-600 sm:grid"><span>Product</span><span>Quantity</span><span>Expiration</span><span>Status</span></div>{lots.map((lot) => <div key={lot.id} className="grid gap-2 border-b border-sage-100 px-5 py-4 last:border-0 sm:grid-cols-[1.4fr_0.7fr_1fr_0.8fr] sm:items-center sm:gap-4"><div><p className="font-bold text-sage-950">{lot.product}</p><p className="text-xs text-sage-500">Lot {lot.id}</p></div><span className="text-sm text-sage-800">{lot.quantity} units</span><span className="text-sm text-sage-800">{lot.expiry}</span><span className={`w-fit rounded-full px-2.5 py-1 text-xs font-semibold ${lot.expiring ? 'bg-amber-100 text-amber-900' : 'bg-emerald-100 text-emerald-900'}`}>{lot.expiring ? 'Expiring soon' : 'Good'}</span></div>)}</div></div>
}
