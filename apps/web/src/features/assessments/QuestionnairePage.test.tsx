import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import i18n from '@/lib/i18n';
import { jsonResponse, TestProviders } from '../../../tests/render';
import type { AssessmentResult, Instrument } from './api';
import { QuestionnairePage } from './QuestionnairePage';

const OPTIONS = ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'];

function phq9(overrides: Partial<Instrument> = {}): Instrument {
  return {
    type: 'PHQ9',
    title: 'PHQ-9',
    stem: 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
    items: Array.from({ length: 9 }, (_, index) => ({ index, text: `Item ${index + 1}` })),
    options: OPTIONS.map((label, value) => ({ value, label })),
    difficulty_question: 'How difficult have these problems made it?',
    difficulty_options: [
      'Not difficult at all',
      'Somewhat difficult',
      'Very difficult',
      'Extremely difficult',
    ].map((label, value) => ({ value, label })),
    item_locale: 'en',
    requested_locale: 'en',
    translation_available: true,
    attribution: 'No permission required to reproduce.',
    ...overrides,
  };
}

function result(overrides: Partial<AssessmentResult> = {}): AssessmentResult {
  return {
    id: 'a1',
    type: 'PHQ9',
    total: 1,
    max_score: 27,
    severity_band: 'minimal',
    next_step: 'consult_professional',
    safety_item_positive: true,
    functional_difficulty: null,
    created_at: '2026-10-20T10:00:00Z',
    ...overrides,
  };
}

function mockApi(instrument: Instrument, saved: AssessmentResult) {
  const fetchMock = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>((url) => {
    if (url.includes('/items')) return Promise.resolve(jsonResponse(instrument));
    if (url.includes('/safety/resources')) return Promise.reject(new TypeError('offline'));
    return Promise.resolve(jsonResponse(saved, 201));
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function renderPage() {
  const router = createMemoryRouter(
    [{ path: '/app/assessments/:type', element: <QuestionnairePage /> }],
    { initialEntries: ['/app/assessments/PHQ9'] },
  );
  render(
    <TestProviders>
      <RouterProvider router={router} />
    </TestProviders>,
  );
}

async function answer(label: string) {
  await userEvent.click(screen.getByRole('radio', { name: label }));
}

async function next() {
  await userEvent.click(screen.getByRole('button', { name: 'Next' }));
}

describe('QuestionnairePage', () => {
  afterEach(async () => {
    await i18n.changeLanguage('en');
  });

  it('opens the crisis card as soon as item 9 is answered above zero', async () => {
    mockApi(phq9(), result());
    renderPage();

    await screen.findByRole('heading', { name: 'Item 1' });
    for (let i = 0; i < 8; i += 1) {
      await answer('Not at all');
      await next();
    }
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await answer('Several days');

    const dialog = await screen.findByRole('dialog', {
      name: "You don't have to go through this alone.",
    });
    // Still on item 9: the crisis card arrives before any result is shown.
    expect(screen.getByRole('heading', { name: 'Item 9', hidden: true })).toBeInTheDocument();
    expect(
      within(dialog).getByRole('link', { name: /Call Tele-MANAS now: 14416/ }),
    ).toHaveAttribute('href', 'tel:14416');
  });

  it('submits every answer plus the difficulty rating and shows the result', async () => {
    const fetchMock = mockApi(
      phq9(),
      result({
        total: 10,
        severity_band: 'moderate',
        next_step: 'talk_to_someone',
        safety_item_positive: false,
      }),
    );
    renderPage();

    await screen.findByRole('heading', { name: 'Item 1' });
    const picks = [
      'Several days',
      'More than half the days',
      'Several days',
      'More than half the days',
      'Several days',
      'Several days',
      'Several days',
      'Several days',
      'Not at all',
    ];
    for (const pick of picks) {
      await answer(pick);
      await next();
    }
    await answer('Somewhat difficult');
    await userEvent.click(screen.getByRole('button', { name: 'See my result' }));

    expect(await screen.findByRole('heading', { name: 'Moderate range' })).toBeInTheDocument();
    expect(screen.getByText('This is a screening result, not a diagnosis.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Talk to someone' })).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST');
    expect(post?.[0]).toBe('/api/v1/assessments/PHQ9');
    expect(JSON.parse(post?.[1]?.body as string)).toEqual({
      answers: [1, 2, 1, 2, 1, 1, 1, 1, 0],
      functional_difficulty: 1,
    });
  });

  it('cannot move on without an answer', async () => {
    mockApi(phq9(), result());
    renderPage();
    await screen.findByRole('heading', { name: 'Item 1' });
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
  });

  it('says plainly when items are in English because no validated Tamil version exists', async () => {
    await i18n.changeLanguage('ta');
    mockApi(phq9({ requested_locale: 'ta', translation_available: false }), result());
    renderPage();

    const item = await screen.findByRole('heading', { name: 'Item 1' });
    expect(item).toHaveAttribute('lang', 'en');
    expect(screen.getByText(/தமிழ்ப் பதிப்பு இன்னும் சேர்க்கப்படவில்லை/)).toBeInTheDocument();
  });
});
