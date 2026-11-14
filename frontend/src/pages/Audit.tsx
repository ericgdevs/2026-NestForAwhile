import { useState } from 'react'
import { BarcodeScanner } from '../components/BarcodeScanner'

export function Audit() {
  const [code, setCode] = useState('')
  const [actual, setActual] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const expected = 8
  const variance = actual === '' ? null : Number(actual) - expected
  return <div className="mx-auto max-w-3xl"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Warehouse tools</p><h1 className="mt-2 text-3xl font-bold text-sage-950">Inventory audit</h1><p className="mt-3 text-sage-700">Scan an item, compare the shelf count, and record the variance.</p><div className="mt-8"><BarcodeScanner onDetected={(value) => { setCode(value); setConfirmed(false) }} /></div>{code && <section className="mt-6 rounded-3xl border border-sage-200 bg-white p-6"><p className="text-sm text-sage-600">Item code {code}</p><h2 className="mt-1 text-xl font-bold text-sage-950">Brown rice</h2><p className="mt-4 text-sm text-sage-700">Current system count: <strong>{expected}</strong></p><label className="mt-5 block text-sm font-semibold text-sage-950">Actual count<input className="mt-2 w-full rounded-xl border border-sage-300 px-3 py-3" type="number" min="0" value={actual} onChange={(event) => { setActual(event.target.value); setConfirmed(false) }} /></label>{variance !== null && <p className={`mt-4 rounded-xl p-3 text-sm font-semibold ${variance === 0 ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-900'}`}>Variance: {variance > 0 ? '+' : ''}{variance}</p>}{variance !== null && <button className="mt-5 rounded-xl bg-sage-700 px-4 py-3 font-semibold text-white" onClick={() => setConfirmed(true)}>Confirm count</button>}{confirmed && <p role="status" className="mt-4 text-sm font-semibold text-sage-700">Audit saved. Inventory has been updated.</p>}</section>}</div>
}
