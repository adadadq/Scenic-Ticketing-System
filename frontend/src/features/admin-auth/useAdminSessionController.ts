import { useState } from 'react'
import type { AdminLoginRequest, AdminMe } from '../../shared/api/types'
import { useAdminLoginMutation, useAdminLogoutMutation, useAdminSessionQuery } from './queries'

export type AdminAuthMode = 'mock' | 'api'

type LoginCallbacks = {
  onSuccess?: (admin: AdminMe) => void
}

const adminAuthMode: AdminAuthMode = import.meta.env.VITE_ADMIN_AUTH_MODE === 'api' ? 'api' : 'mock'

function createMockAdmin(body: AdminLoginRequest): AdminMe {
  return {
    adminUserId: 1,
    displayName: body.username === 'admin' ? '演示管理员' : body.username,
    role: 'SUPER_ADMIN',
    username: body.username,
  }
}

export function useAdminSessionController() {
  const isApiMode = adminAuthMode === 'api'
  const [mockAdmin, setMockAdmin] = useState<AdminMe | null>(null)
  const sessionQuery = useAdminSessionQuery({ enabled: isApiMode })
  const loginMutation = useAdminLoginMutation()
  const logoutMutation = useAdminLogoutMutation()
  const admin = isApiMode ? sessionQuery.data ?? null : mockAdmin

  function login(body: AdminLoginRequest, callbacks: LoginCallbacks = {}) {
    if (isApiMode) {
      loginMutation.mutate(body, {
        onSuccess: (nextAdmin) => {
          callbacks.onSuccess?.(nextAdmin)
        },
      })
      return
    }

    const nextAdmin = createMockAdmin(body)
    setMockAdmin(nextAdmin)
    callbacks.onSuccess?.(nextAdmin)
  }

  function logout() {
    if (isApiMode) {
      logoutMutation.mutate()
      return
    }

    setMockAdmin(null)
  }

  return {
    admin,
    authMode: adminAuthMode,
    isLoginPending: isApiMode ? loginMutation.isPending : false,
    isLogoutPending: isApiMode ? logoutMutation.isPending : false,
    isSessionLoading: isApiMode ? sessionQuery.isLoading : false,
    login,
    loginError: isApiMode ? loginMutation.error : null,
    logout,
    logoutError: isApiMode ? logoutMutation.error : null,
    sessionError: isApiMode ? sessionQuery.error : null,
  }
}
