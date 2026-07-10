import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { ApiError, resetCsrfToken } from '../../shared/api/client'
import { adminAuthApi } from '../../shared/api/endpoints'
import type { AdminLoginRequest, AdminMe, AdminProfileUpdateRequest } from '../../shared/api/types'
import { authQueryKeys } from '../auth/queries'

export const adminAuthQueryKeys = {
  me: ['admin-auth', 'me'] as const,
}

export type AdminSession = AdminMe | null

async function resetVisitorSession(queryClient: QueryClient) {
  await queryClient.cancelQueries({ queryKey: ['orders'] })
  queryClient.setQueryData(authQueryKeys.me, null)
  await queryClient.resetQueries({ queryKey: ['orders'] })
}

async function getAdminSession(): Promise<AdminSession> {
  try {
    return await adminAuthApi.me()
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.code === 'ADMIN_AUTH_REQUIRED' || error.code === 'ADMIN_FORBIDDEN')
    ) {
      return null
    }

    throw error
  }
}

export function useAdminSessionQuery(options: { enabled?: boolean } = {}) {
  return useQuery({
    enabled: options.enabled ?? true,
    queryFn: getAdminSession,
    queryKey: adminAuthQueryKeys.me,
    retry: false,
  })
}

export function useAdminLoginMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: AdminLoginRequest) => adminAuthApi.login(body),
    onSuccess: async (admin) => {
      resetCsrfToken()
      queryClient.setQueryData(adminAuthQueryKeys.me, admin)
      await resetVisitorSession(queryClient)
    },
  })
}

export function useAdminProfileUpdateMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: AdminProfileUpdateRequest) => adminAuthApi.updateProfile(body),
    onSuccess: (admin, body) => {
      if (body.newPassword) {
        resetCsrfToken()
        queryClient.setQueryData(adminAuthQueryKeys.me, null)
        return
      }
      queryClient.setQueryData(adminAuthQueryKeys.me, admin)
    },
  })
}

export function useAdminLogoutMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => adminAuthApi.logout(),
    onSuccess: async () => {
      resetCsrfToken()
      queryClient.setQueryData(adminAuthQueryKeys.me, null)
      await resetVisitorSession(queryClient)
    },
  })
}
