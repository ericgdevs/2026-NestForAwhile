import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Agentation } from 'agentation'
import { AppShell } from './components/AppShell'
import { AuthProvider, ProtectedRoute } from './lib/auth'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Placeholder } from './pages/Placeholder'
import { Unauthorized } from './pages/Unauthorized'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route index element={<Home />} />
              <Route path="/home" element={<Home />} />
              <Route path="/scan" element={<Placeholder title="Scan an item" message="Scan a barcode or enter a product code to see a friendly nutrition and availability check." />} />
              <Route path="/cart" element={<Placeholder title="My cart" message="Items you choose during your visit will collect here for an easy checkout." />} />
              <Route path="/inventory" element={<Placeholder title="Inventory" message="Warehouse inventory tools will appear here for staff and volunteers." />} />
              <Route path="/unauthorized" element={<Unauthorized />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Agentation />
      </AuthProvider>
    </BrowserRouter>
  )
}
