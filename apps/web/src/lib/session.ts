import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError, apiFetch } from '@/lib/api';
import type { Locale } from '@/lib/i18n';

export type ConsentScope =
  'core' | 'chat_history' | 'voice' | 'wearables' | 'cloud_llm' | 'reminders';

export const OPTIONAL_SCOPES: Exclude<ConsentScope, 'core'>[] = [
  'chat_history',
  'voice',
  'wearables',
  'cloud_llm',
  'reminders',
];

export type ConsentChoices = { core: true } & Partial<Record<ConsentScope, boolean>>;

export interface SessionUser {
  id: string;
  is_anonymous: boolean;
  email: string | null;
  locale: Locale;
  created_at: string;
}

export interface ConsentItem {
  scope: ConsentScope;
  granted: boolean;
  required: boolean;
  version: string | null;
  granted_at: string | null;
  revoked_at: string | null;
}

export interface ConsentsResponse {
  current_version: string;
  items: ConsentItem[];
}

const SESSION_KEY = ['session'] as const;
const CONSENTS_KEY = ['consents'] as const;

/** The signed-in user, or `null` when there is no valid session. */
export function useSession() {
  return useQuery({
    queryKey: SESSION_KEY,
    queryFn: async ({ signal }) => {
      try {
        return await apiFetch<SessionUser>('/auth/me', { signal });
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    staleTime: 60_000,
  });
}

function useSetSession() {
  const client = useQueryClient();
  return (user: SessionUser | null) => {
    client.setQueryData(SESSION_KEY, user);
    void client.invalidateQueries({ queryKey: CONSENTS_KEY });
  };
}

export function useStartAnonymous() {
  const setSession = useSetSession();
  return useMutation({
    mutationFn: (input: { locale: Locale; consents: ConsentChoices }) =>
      apiFetch<SessionUser>('/auth/anonymous', {
        method: 'POST',
        body: { age_confirmed: true, ...input },
      }),
    onSuccess: setSession,
  });
}

export function useLogin() {
  const setSession = useSetSession();
  return useMutation({
    mutationFn: (input: { email: string; password: string }) =>
      apiFetch<SessionUser>('/auth/login', { method: 'POST', body: input }),
    onSuccess: setSession,
  });
}

export function useUpgrade() {
  const setSession = useSetSession();
  return useMutation({
    mutationFn: (input: { email: string; password: string }) =>
      apiFetch<SessionUser>('/auth/upgrade', { method: 'POST', body: input }),
    onSuccess: setSession,
  });
}

export function useLogout() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<undefined>('/auth/logout', { method: 'POST' }),
    onSettled: () => {
      client.clear();
      client.setQueryData(SESSION_KEY, null);
    },
  });
}

export function useSaveLocale() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (locale: Locale) =>
      apiFetch<SessionUser>('/auth/me/locale', { method: 'PUT', body: { locale } }),
    onSuccess: (user) => client.setQueryData(SESSION_KEY, user),
  });
}

export function useConsents() {
  return useQuery({
    queryKey: CONSENTS_KEY,
    queryFn: ({ signal }) => apiFetch<ConsentsResponse>('/consents', { signal }),
  });
}

export function useUpdateConsents() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (consents: Partial<Record<ConsentScope, boolean>>) =>
      apiFetch<ConsentsResponse>('/consents', { method: 'PUT', body: { consents } }),
    onSuccess: (data) => client.setQueryData(CONSENTS_KEY, data),
  });
}
