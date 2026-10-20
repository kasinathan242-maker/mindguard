import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { jsonResponse, renderWithProviders } from '../../../tests/render';
import { StatusPage } from './StatusPage';

describe('StatusPage', () => {
  it('shows healthy services reported by the API', async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse({
          status: 'ok',
          version: '0.1.0',
          checks: { database: 'ok', redis: 'ok' },
        }),
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    renderWithProviders(<StatusPage />);

    expect(await screen.findByText('All services are running')).toBeInTheDocument();
    expect(screen.getByText('Version 0.1.0')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/health', expect.anything());
  });

  it('says the API is unreachable when the request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse({ detail: 'x' }, 404))),
    );

    renderWithProviders(<StatusPage />);

    expect(await screen.findByText('The API cannot be reached')).toBeInTheDocument();
  });
});
