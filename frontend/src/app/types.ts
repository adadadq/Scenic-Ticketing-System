export type VisitorPage = 'booking' | 'orders' | 'service'
export type AdminPage = 'admin' | 'tickets' | 'reports' | 'orders' | 'audit' | 'settings'
export type AppPage = VisitorPage | AdminPage
export type AppRoute =
  | { mode: 'visitor'; page: VisitorPage }
  | { mode: 'admin'; page: AdminPage }
