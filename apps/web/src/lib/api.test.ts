import { describe, expect, it, vi } from 'vitest';
import { jsonResponse } from '../../tests/render';
import { ApiError, apiFetch } from './api';

describe('apiFetch', () => {
  it('refreshes the session once on 401 and retries the request', async () => {
    const fetchMock = vi
      .fn<(input: string, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(jsonResponse({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(jsonResponse({ id: 'u1' }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await apiFetch<{ ok: boolean }>('/consents');

    expect(result).toEqual({ ok: true });
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      '/api/v1/consents',
      '/api/v1/auth/refresh',
      '/api/v1/consents',
    ]);
  });

  it('shares one refresh between concurrent 401s', async () => {
    const fetchMock = vi.fn((input: string) => {
      if (input === '/api/v1/auth/refresh') return Promise.resolve(jsonResponse({}, 200));
      return Promise.resolve(jsonResponse({ detail: 'expired' }, 401));
    });
    vi.stubGlobal('fetch', fetchMock);

    await Promise.allSettled([apiFetch('/a'), apiFetch('/b')]);

    const refreshes = fetchMock.mock.calls.filter(([url]) => url === '/api/v1/auth/refresh');
    expect(refreshes).toHaveLength(1);
  });

  it('does not try to refresh after a failed sign-in', async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(jsonResponse({ detail: 'Email or password is incorrect' }, 401)),
    );
    vi.stubGlobal('fetch', fetchMock);

    const error: unknown = await apiFetch('/auth/login', { method: 'POST', body: {} }).catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).serverMessage).toBe('Email or password is incorrect');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
