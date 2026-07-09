import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { announcementsApi } from '../../shared/api/endpoints'
import type { AnnouncementPublishRequest } from '../../shared/api/types'

export const announcementQueryKeys = {
  current: ['announcements', 'current'] as const,
}

export function useCurrentAnnouncementQuery() {
  return useQuery({
    queryKey: announcementQueryKeys.current,
    queryFn: () => announcementsApi.current(),
    retry: false,
  })
}

export function usePublishAnnouncementMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: AnnouncementPublishRequest) => announcementsApi.publish(body),
    onSuccess: (notice) => {
      queryClient.setQueryData(announcementQueryKeys.current, notice)
    },
  })
}
