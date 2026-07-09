import { useEffect, useState } from 'react'
import './App.css'
import { AdminAppShell } from './app/AdminAppShell'
import type { AdminPage, AppRoute, VisitorPage } from './app/types'
import { VisitorAppShell } from './app/VisitorAppShell'
import { AdminLoginGate, AdminWorkbench } from './features/admin/AdminWorkbench'
import { useAdminSessionController } from './features/admin-auth/useAdminSessionController'
import type { AuthMode } from './features/auth/AuthStatus'
import { BookingWorkbench } from './features/booking/BookingWorkbench'
import { OrdersWorkbench } from './features/orders/OrdersWorkbench'
import { VisitorServiceWorkbench } from './features/visitor-service/VisitorServiceWorkbench'

const adminPages: AdminPage[] = ['admin', 'tickets', 'reports', 'orders', 'audit', 'settings']
const visitorPages: VisitorPage[] = ['booking', 'orders', 'service']

function readRouteFromHash(): AppRoute {
  const hash = window.location.hash.replace(/^#\/?/, '')
  const [mode, page] = hash.split('/')

  if (mode === 'admin') {
    return { mode: 'admin', page: adminPages.includes(page as AdminPage) ? page as AdminPage : 'admin' }
  }

  if (mode === 'visitor' && visitorPages.includes(page as VisitorPage)) {
    return { mode: 'visitor', page: page as VisitorPage }
  }

  return { mode: 'visitor', page: 'booking' }
}

function writeRouteToHash(route: AppRoute) {
  const nextHash = route.mode === 'admin'
    ? route.page === 'admin' ? '#/admin' : `#/admin/${route.page}`
    : `#/visitor/${route.page}`

  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash
  }
}

function App() {
  const [route, setRoute] = useState<AppRoute>(() => readRouteFromHash())
  const [authDialogRequest, setAuthDialogRequest] = useState<{ mode: AuthMode; requestId: number }>()

  useEffect(() => {
    function syncRouteFromHash() {
      const nextRoute = readRouteFromHash()
      setRoute(nextRoute)
      writeRouteToHash(nextRoute)
    }

    window.addEventListener('hashchange', syncRouteFromHash)
    syncRouteFromHash()
    return () => window.removeEventListener('hashchange', syncRouteFromHash)
  }, [])

  function openAuthDialog(mode: AuthMode) {
    setAuthDialogRequest((request) => ({
      mode,
      requestId: (request?.requestId ?? 0) + 1,
    }))
  }

  function openVisitorPage(page: VisitorPage) {
    const nextRoute = { mode: 'visitor', page } as const
    setRoute(nextRoute)
    writeRouteToHash(nextRoute)
  }

  function openAdminPage(page: AdminPage) {
    const nextRoute = { mode: 'admin', page } as const
    setRoute(nextRoute)
    writeRouteToHash(nextRoute)
  }

  if (route.mode === 'admin') {
    return (
      <AdminRoute
        activePage={route.page}
        onOpenPage={openAdminPage}
        onOpenVisitor={() => openVisitorPage('booking')}
      />
    )
  }

  return (
    <VisitorAppShell activePage={route.page} authDialogRequest={authDialogRequest} onPageChange={openVisitorPage}>
      {route.page === 'booking' && (
        <BookingWorkbench
          onOpenAuth={openAuthDialog}
          onOpenOrders={() => openVisitorPage('orders')}
          onOpenService={() => openVisitorPage('service')}
        />
      )}
      {route.page === 'orders' && (
        <OrdersWorkbench
          onOpenAuth={() => openAuthDialog('login')}
          onOpenBooking={() => openVisitorPage('booking')}
          onOpenService={() => openVisitorPage('service')}
        />
      )}
      {route.page === 'service' && (
        <VisitorServiceWorkbench
          onOpenBooking={() => openVisitorPage('booking')}
          onOpenOrders={() => openVisitorPage('orders')}
        />
      )}
    </VisitorAppShell>
  )
}

function AdminRoute({
  activePage,
  onOpenPage,
  onOpenVisitor,
}: {
  activePage: AdminPage
  onOpenPage: (page: AdminPage) => void
  onOpenVisitor: () => void
}) {
  const adminSession = useAdminSessionController()
  const activeError = adminSession.loginError ?? adminSession.logoutError ?? adminSession.sessionError

  if (!adminSession.admin) {
    return (
      <AdminLoginGate
        activeError={activeError}
        authMode={adminSession.authMode}
        isLoginPending={adminSession.isLoginPending}
        onOpenVisitor={onOpenVisitor}
        onSubmit={(values) => adminSession.login(values)}
      />
    )
  }

  return (
    <AdminAppShell
      activePage={activePage}
      admin={adminSession.admin}
      isLogoutPending={adminSession.isLogoutPending}
      logout={adminSession.logout}
      onOpenVisitor={onOpenVisitor}
      onPageChange={onOpenPage}
    >
      <AdminWorkbench
        activePage={activePage}
        admin={adminSession.admin}
        authMode={adminSession.authMode}
        isLogoutPending={adminSession.isLogoutPending}
        isProfileUpdatePending={adminSession.isProfileUpdatePending}
        isSessionLoading={adminSession.isSessionLoading}
        logout={adminSession.logout}
        logoutError={adminSession.logoutError}
        onOpenPage={onOpenPage}
        onResetProfileUpdateError={adminSession.resetProfileUpdateError}
        onUpdateProfile={adminSession.updateProfile}
        profileUpdateError={adminSession.profileUpdateError}
        sessionError={adminSession.sessionError}
      />
    </AdminAppShell>
  )
}

export default App
