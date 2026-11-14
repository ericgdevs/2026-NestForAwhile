import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Agentation } from 'agentation'
import { AppShell } from './components/AppShell'
import { AuthProvider, ProtectedRoute } from './lib/auth'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Placeholder } from './pages/Placeholder'
import { Profile } from './pages/Profile'
import { Scan } from './pages/Scan'
import { Cart } from './pages/Cart'
import { CartProvider } from './lib/cart'
import { Recipes } from './pages/Recipes'
import { Checkout } from './pages/Checkout'
import { Audit } from './pages/Audit'
import { Unauthorized } from './pages/Unauthorized'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route index element={<Home />} />
              <Route path="/home" element={<Home />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/scan" element={<Scan />} />
              <Route path="/cart" element={<Cart />} />
              <Route path="/recipes" element={<Recipes />} />
              <Route path="/checkout" element={<Checkout />} />
              <Route path="/audit" element={<Audit />} />
              <Route path="/inventory" element={<Placeholder title="Inventory" message="Warehouse inventory tools will appear here for staff and volunteers." />} />
              <Route path="/unauthorized" element={<Unauthorized />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </CartProvider>
        <Agentation />
      </AuthProvider>
    </BrowserRouter>
  )
}
