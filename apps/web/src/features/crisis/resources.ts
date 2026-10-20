import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiFetch } from '@/lib/api';
import type { Locale } from '@/lib/i18n';
import fallback from './fallback.json';

export interface CrisisResource {
  id: string;
  kind: 'helpline' | 'emergency';
  name: string;
  description: string;
  display_number: string;
  dial: string;
  alternate_display_number: string | null;
  alternate_dial: string | null;
}

const FALLBACK = fallback as Record<Locale, CrisisResource[]>;

/**
 * Crisis resources from the API, with the bundled copy shown immediately and used whenever the
 * network or API is unavailable. The card must never wait on, or fail because of, a request.
 */
export function useCrisisResources(): CrisisResource[] {
  const { i18n } = useTranslation();
  const locale: Locale = i18n.language === 'ta' ? 'ta' : 'en';
  const { data } = useQuery({
    queryKey: ['crisis-resources', locale],
    queryFn: ({ signal }) =>
      apiFetch<CrisisResource[]>(`/safety/resources?locale=${locale}`, { signal }),
    placeholderData: FALLBACK[locale],
    staleTime: 60 * 60 * 1000,
    retry: false,
  });
  return data ?? FALLBACK[locale];
}
