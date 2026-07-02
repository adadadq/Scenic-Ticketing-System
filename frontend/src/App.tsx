import { useState } from 'react'
import './App.css'
import { AppShell } from './app/AppShell'
import type { AppPage } from './app/types'
import { AdminWorkbench } from './features/admin/AdminWorkbench'
import type { AuthMode } from './features/auth/AuthStatus'
import { BookingWorkbench } from './features/booking/BookingWorkbench'
import { OrdersWorkbench } from './features/orders/OrdersWorkbench'

function App() {
  const [activePage, setActivePage] = useState<AppPage>('booking')
  const [authDialogRequest, setAuthDialogRequest] = useState<{ mode: AuthMode; requestId: number }>()

  function openAuthDialog(mode: AuthMode) {
    setAuthDialogRequest((request) => ({
      mode,
      requestId: (request?.requestId ?? 0) + 1,
    }))
  }

  return (
    <AppShell activePage={activePage} authDialogRequest={authDialogRequest} onPageChange={setActivePage}>
      {activePage === 'booking' ? (
        <BookingWorkbench onOpenAuth={openAuthDialog} onOpenOrders={() => setActivePage('orders')} />
      ) : activePage === 'orders' ? (
        <OrdersWorkbench onOpenAuth={() => openAuthDialog('login')} onOpenBooking={() => setActivePage('booking')} />
      ) : (
        <AdminWorkbench />
      )}
    </AppShell>
  )
}

export default App
