import { useState } from 'react'
import { BarcodeScanner } from '../components/BarcodeScanner'
import { StatusBadge } from '../components/StatusBadge'

const products = {
  '012345': { name: 'Brown rice', status: 'green' as const, label: 'Good to go', explanation: 'A pantry staple that fits your current preferences.', nutrition: '160 calories · 0 mg sodium per serving' },
  '678901': { name: 'Canned tomato soup', status: 'yellow' as const, label: 'Review needed', explanation: 'This item is higher in sodium. A volunteer can help you compare options.', nutrition: '180 calories · 680 mg sodium per serving' },
  '999999': { name: 'Peanut snack mix', status: 'red' as const, label: 'Not available', explanation: 'This item contains an allergen in your profile.', nutrition: '210 calories · 12 g protein per serving' },
}

export function Scan() {
  const [code, setCode] = useState('')
  const [searched, setSearched] = useState(false)
  const product = products[code as keyof typeof products]

  function handleDetected(value: string) {
    setCode(value)
    setSearched(true)
  }

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Safety check</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-sage-950">Scan an item</h1>
      <p className="mt-3 text-sage-700">We’ll show what we know about an item and explain what the result means.</p>
      <div className="mt-8"><BarcodeScanner onDetected={handleDetected} /></div>
      {searched && product && <section className="mt-6 rounded-3xl border border-sage-200 bg-white p-6 shadow-sm"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start"><div><p className="text-sm text-sage-600">Product code {code}</p><h2 className="mt-1 text-2xl font-bold text-sage-950">{product.name}</h2></div><StatusBadge status={product.status} label={product.label} /></div><p className="mt-5 text-sage-800">{product.explanation}</p><p className="mt-4 rounded-xl bg-sage-50 p-4 text-sm font-semibold text-sage-800">{product.nutrition}</p></section>}
      {searched && !product && <div role="alert" className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">We couldn’t find that item yet. Please check the code or ask a volunteer for help.</div>}
    </div>
  )
}
