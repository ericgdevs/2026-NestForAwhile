import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

export type CartItem = { productId: number; name: string; quantity: number }
type CartContextValue = { items: CartItem[]; addItem: (item: Omit<CartItem, 'quantity'>) => void; updateQuantity: (productId: number, quantity: number) => void; removeItem: (productId: number) => void }
const CartContext = createContext<CartContextValue | null>(null)

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([])
  const value = useMemo(() => ({
    items,
    addItem: (item: Omit<CartItem, 'quantity'>) => setItems((current) => {
      const existing = current.find((entry) => entry.productId === item.productId)
      return existing ? current.map((entry) => entry.productId === item.productId ? { ...entry, quantity: entry.quantity + 1 } : entry) : [...current, { ...item, quantity: 1 }]
    }),
    updateQuantity: (productId: number, quantity: number) => setItems((current) => current.map((item) => item.productId === productId ? { ...item, quantity: Math.max(1, quantity) } : item)),
    removeItem: (productId: number) => setItems((current) => current.filter((item) => item.productId !== productId)),
  }), [items])
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const context = useContext(CartContext)
  if (!context) throw new Error('useCart must be used within CartProvider')
  return context
}
