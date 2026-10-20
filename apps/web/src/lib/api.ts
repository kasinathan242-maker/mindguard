export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(`Request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }

  /** The server's human-readable message, when it sent one. */
  get serverMessage(): string | null {
    if (this.detail && typeof this.detail === 'object' && 'detail' in this.detail) {
      const inner = this.detail.detail;
      if (typeof inner === 'string') return inner;
    }
    return null;
  }
}

const BASE = '/api/v1';

// Requests that must never trigger a silent refresh-and-retry.
const NO_REFRESH = new Set(['/auth/refresh', '/auth/login', '/auth/register', '/auth/anonymous']);

type JsonBody = Record<string, unknown> | unknown[];

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: JsonBody;
  signal?: AbortSignal;
}

let refreshing: Promise<boolean> | null = null;

/** Rotate the session once, sharing the in-flight request between concurrent callers. */
function refreshSession(): Promise<boolean> {
  refreshing ??= fetch(`${BASE}/auth/refresh`, { method: 'POST', credentials: 'include' })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const { method = 'GET', body, signal } = options;
  const init: RequestInit = {
    method,
    credentials: 'include',
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) init.body = JSON.stringify(body);
  if (signal) init.signal = signal;
  return fetch(`${BASE}${path}`, init);
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await send(path, options);

  if (response.status === 401 && !NO_REFRESH.has(path) && (await refreshSession())) {
    response = await send(path, options);
  }

  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
