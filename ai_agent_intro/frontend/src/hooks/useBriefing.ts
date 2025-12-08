import { useQuery } from '@tanstack/react-query';
import { getBriefing } from '../api/client';
import type { BriefingRequest, BriefingResponse } from '../types';

export function useBriefing(request: BriefingRequest | null) {
  return useQuery<BriefingResponse>({
    queryKey: ['briefing', request?.city, request?.date, request?.language],
    queryFn: () => {
      if (!request) throw new Error('No request');
      return getBriefing(request.city, request.date, request.language);
    },
    enabled: !!request,
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
