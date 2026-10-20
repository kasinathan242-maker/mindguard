import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/lib/api';

type CheckStatus = 'ok' | 'unavailable';

export interface Health {
  status: 'ok' | 'degraded';
  version: string;
  checks: { database: CheckStatus; redis: CheckStatus };
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => apiFetch<Health>('/health', { signal }),
    refetchInterval: 15_000,
  });
}
