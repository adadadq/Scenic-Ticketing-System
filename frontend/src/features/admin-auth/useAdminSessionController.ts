import type { AdminLoginRequest, AdminMe, AdminProfileUpdateRequest } from '../../shared/api/types'
import {
  useAdminLoginMutation,
  useAdminLogoutMutation,
  useAdminProfileUpdateMutation,
  useAdminSessionQuery,
} from './queries'

export type AdminAuthMode = 'api'

type LoginCallbacks = {
  onSuccess?: (admin: AdminMe) => void
}

const adminAuthMode: AdminAuthMode = 'api'

export function useAdminSessionController() {
  const sessionQuery = useAdminSessionQuery()
  const loginMutation = useAdminLoginMutation()
  const logoutMutation = useAdminLogoutMutation()
  const profileUpdateMutation = useAdminProfileUpdateMutation()
  const admin = sessionQuery.data ?? null

  function login(body: AdminLoginRequest, callbacks: LoginCallbacks = {}) {
    loginMutation.mutate(body, {
      onSuccess: (nextAdmin) => {
        callbacks.onSuccess?.(nextAdmin)
      },
    })
  }

  function logout() {
    logoutMutation.mutate()
  }

  function updateProfile(body: AdminProfileUpdateRequest, callbacks: LoginCallbacks = {}) {
    profileUpdateMutation.mutate(body, {
      onSuccess: (nextAdmin) => {
        callbacks.onSuccess?.(nextAdmin)
      },
    })
  }

  function resetProfileUpdateError() {
    profileUpdateMutation.reset()
  }

  return {
    admin,
    authMode: adminAuthMode,
    isLoginPending: loginMutation.isPending,
    isLogoutPending: logoutMutation.isPending,
    isProfileUpdatePending: profileUpdateMutation.isPending,
    isSessionLoading: sessionQuery.isLoading,
    login,
    loginError: loginMutation.error,
    logout,
    logoutError: logoutMutation.error,
    profileUpdateError: profileUpdateMutation.error,
    resetProfileUpdateError,
    sessionError: sessionQuery.error,
    updateProfile,
  }
}
