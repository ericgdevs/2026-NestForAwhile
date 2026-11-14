import { Home, LogOut, Menu, PackageCheck, ScanLine, ShoppingBasket, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { cn } from '../lib/utils'

const navigation = [
  { to: '/', label: 'My recommendations', icon: Home },
  { to: '/scan', label: 'Scan an item', icon: ScanLine },
  { to: '/cart', label: 'My cart', icon: ShoppingBasket },
  { to: '/inventory', label: 'Inventory', icon: PackageCheck },
]

export function AppShell() {
  const [open, setOpen] = useState(false)
  const { user, signOut } = useAuth()

  return (
    <div className="min-h-screen bg-[#f7fbf5]">
      <aside className={cn('fixed inset-y-0 left-0 z-30 w-72 transform border-r border-sage-200 bg-white px-5 py-6 transition-transform lg:translate-x-0', open ? 'translate-x-0' : '-translate-x-full')}>
        <div className="flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <span className="grid size-10 place-items-center rounded-2xl bg-sage-700 text-lg font-bold text-white">N</span>
            <span><strong className="block text-sage-950">Nest For Awhile</strong><small className="text-xs text-sage-600">A little more support</small></span>
          </NavLink>
          <button className="rounded-lg p-2 text-sage-700 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={20} /></button>
        </div>
        <nav className="mt-10 space-y-2" aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)} className={({ isActive }) => cn('flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition-colors', isActive ? 'bg-sage-100 text-sage-950' : 'text-sage-700 hover:bg-sage-50')}>
              <Icon size={19} aria-hidden="true" />{label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute inset-x-5 bottom-6 rounded-2xl bg-sage-50 p-4">
          <p className="text-sm font-semibold text-sage-950">{user?.name}</p>
          <p className="mt-1 text-xs text-sage-600">{user?.role}</p>
          <button className="mt-4 flex items-center gap-2 text-sm font-semibold text-sage-700" onClick={signOut}><LogOut size={16} />Sign out</button>
        </div>
      </aside>
      {open && <button aria-label="Close navigation overlay" className="fixed inset-0 z-20 bg-sage-950/20 lg:hidden" onClick={() => setOpen(false)} />}
      <main className="lg:pl-72">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-sage-100 bg-[#f7fbf5]/95 px-5 py-4 backdrop-blur lg:px-10">
          <button className="rounded-lg p-2 text-sage-800 lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu /></button>
          <div className="ml-auto flex items-center gap-3 text-right"><span className="hidden text-sm text-sage-600 sm:inline">You’re doing great, {user?.name.split(' ')[0]}</span><span className="size-9 rounded-full bg-sage-200 text-center text-sm font-bold leading-9 text-sage-800">{user?.name.charAt(0)}</span></div>
        </header>
        <div className="mx-auto max-w-6xl px-5 py-8 lg:px-10"><Outlet /></div>
      </main>
    </div>
  )
}
