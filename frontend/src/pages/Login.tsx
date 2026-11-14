import { useEffect, type FormEvent } from 'react'
import { useState } from 'react'
import { HeartHandshake } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export function Login() {
  const { user, signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<'invalid' | 'inactive' | null>(null)

  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [navigate, user])

  if (user) return null

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const result = signIn(email, password)
    if (result.ok) navigate(location.state?.from?.pathname ?? '/', { replace: true })
    else setError(result.reason ?? 'invalid')
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[#f7fbf5] px-5 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center"><div className="mx-auto grid size-14 place-items-center rounded-3xl bg-sage-700 text-2xl font-bold text-white"><HeartHandshake /></div><h1 className="mt-5 text-3xl font-bold tracking-tight text-sage-950">Welcome back</h1><p className="mt-2 text-sage-700">Let’s make today’s visit a little easier.</p></div>
        <form className="rounded-3xl border border-sage-200 bg-white p-6 shadow-xl shadow-sage-900/5 sm:p-8" onSubmit={submit}>
          {error && <div role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error === 'inactive' ? 'Your enrollment is not active yet. Please check in with a volunteer.' : 'That email or password did not match our records.'}</div>}
          <label className="block text-sm font-semibold text-sage-950">Email<input className="mt-2 w-full rounded-xl border border-sage-300 px-3 py-3 text-sage-950" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.test" /></label>
          <label className="mt-5 block text-sm font-semibold text-sage-950">Password<input className="mt-2 w-full rounded-xl border border-sage-300 px-3 py-3 text-sage-950" type="password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" /></label>
          <button className="mt-6 w-full rounded-xl bg-sage-700 px-4 py-3 font-semibold text-white transition-colors hover:bg-sage-800" type="submit">Sign in</button>
          <p className="mt-5 text-center text-xs text-sage-600">Demo: demo@example.test · welcome</p>
        </form>
      </div>
    </main>
  )
}
