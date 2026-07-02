import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, resetCsrfToken } from '../../shared/api/client'
import { authApi } from '../../shared/api/endpoints'
import type { VisitorLoginRequest, VisitorMe, VisitorRegisterRequest } from '../../shared/api/types'

export const authQueryKeys = {
  me: ['auth', 'me'] as const,
}

export type VisitorSession = VisitorMe | null

async function resetOrderQueries(queryClient: ReturnType<typeof useQueryClient>) {
  await queryClient.cancelQueries({ queryKey: ['orders'] })
  await queryClient.resetQueries({ queryKey: ['orders'] })
}

async function getVisitorSession(): Promise<VisitorSession> {
  try {
    return await authApi.me()
  } catch (error) {
    if (error instanceof ApiError && error.code === 'AUTH_REQUIRED') {
      return null
    }

    throw error
  }
}

export function useVisitorSessionQuery() {
  return useQuery({
    queryKey: authQueryKeys.me,
    queryFn: getVisitorSession,
    retry: false,
  })
}

export function useVisitorLoginMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: VisitorLoginRequest) => authApi.visitorLogin(body),
    onSuccess: async (visitor) => {
      resetCsrfToken()
      queryClient.setQueryData(authQueryKeys.me, visitor)
      await resetOrderQueries(queryClient)
    },
  })
}

export function useVisitorRegisterMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: VisitorRegisterRequest) => authApi.visitorRegister(body),
    onSuccess: async (visitor) => {
      resetCsrfToken()
      queryClient.setQueryData(authQueryKeys.me, visitor)
      await resetOrderQueries(queryClient)
    },
  })
}

export function useVisitorLogoutMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: async () => {
      resetCsrfToken()
      queryClient.setQueryData(authQueryKeys.me, null)
      await resetOrderQueries(queryClient)
    },
  })
}
