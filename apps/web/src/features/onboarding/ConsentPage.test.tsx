import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { describe, expect, it, vi } from 'vitest';
import { jsonResponse, TestProviders } from '../../../tests/render';
import { ConsentPage } from './ConsentPage';

function renderConsent(state: unknown) {
  const router = createMemoryRouter(
    [
      { path: '/start', element: <p>age gate</p> },
      { path: '/start/consent', element: <ConsentPage /> },
      { path: '/app', element: <p>dashboard</p> },
    ],
    { initialEntries: [{ pathname: '/start/consent', state }] },
  );
  render(
    <TestProviders>
      <RouterProvider router={router} />
    </TestProviders>,
  );
}

describe('ConsentPage', () => {
  it('sends people who skipped the age question back to it', () => {
    renderConsent(null);
    expect(screen.getByText('age gate')).toBeInTheDocument();
  });

  it('starts with every optional scope off and core unchecked', () => {
    renderConsent({ ageConfirmed: true });
    const switches = screen.getAllByRole('switch');
    expect(switches).toHaveLength(6);
    for (const control of switches) expect(control).toHaveAttribute('aria-checked', 'false');
  });

  it('requires core consent before creating a session', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    renderConsent({ ageConfirmed: true });

    await userEvent.click(screen.getByRole('button', { name: 'Continue anonymously' }));

    expect(screen.getByText('Please switch on the first item to continue.')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('creates an anonymous session with exactly the chosen consents', async () => {
    const fetchMock = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>(() =>
      Promise.resolve(
        jsonResponse(
          { id: 'u1', is_anonymous: true, email: null, locale: 'en', created_at: '' },
          201,
        ),
      ),
    );
    vi.stubGlobal('fetch', fetchMock);
    renderConsent({ ageConfirmed: true });

    await userEvent.click(
      screen.getByRole('switch', { name: /Store my check-in answers and scores/ }),
    );
    await userEvent.click(screen.getByRole('switch', { name: 'Keep chat history' }));
    await userEvent.click(screen.getByRole('button', { name: 'Continue anonymously' }));

    expect(await screen.findByText('dashboard')).toBeInTheDocument();
    const [url, init] = fetchMock.mock.calls[0] ?? [];
    expect(url).toBe('/api/v1/auth/anonymous');
    expect(JSON.parse(init?.body as string)).toEqual({
      age_confirmed: true,
      locale: 'en',
      consents: {
        core: true,
        chat_history: true,
        voice: false,
        wearables: false,
        cloud_llm: false,
        reminders: false,
      },
    });
  });
});
