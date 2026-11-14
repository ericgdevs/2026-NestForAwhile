import { Link } from 'react-router-dom'

export function Unauthorized() {
  return <div className="mx-auto max-w-lg rounded-3xl border border-sage-200 bg-white p-8 text-center"><h1 className="text-2xl font-bold text-sage-950">That page is not part of your visit</h1><p className="mt-3 text-sage-700">Let’s get you back to the things you can use today.</p><Link className="mt-6 inline-block rounded-xl bg-sage-700 px-4 py-3 font-semibold text-white" to="/">Back home</Link></div>
}
