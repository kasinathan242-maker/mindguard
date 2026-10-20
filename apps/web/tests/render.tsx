import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderResult } from '@testing-library/react';
import { useState, type ReactElement, type ReactNode } from 'react';
import { MemoryRouter } from 'react-router';
import { CrisisProvider } from '@/features/crisis/CrisisProvider';

export function renderWithProviders(ui: ReactElement, { route = '/' } = {}): RenderResult {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <CrisisProvider>
        <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
      </CrisisProvider>
    </QueryClientProvider>,
  );
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export function TestProviders({ children }: { children: ReactNode }) {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  );
  return (
    <QueryClientProvider client={client}>
      <CrisisProvider>{children}</CrisisProvider>
    </QueryClientProvider>
  );
}
