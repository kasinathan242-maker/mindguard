import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { renderWithProviders } from '../../../tests/render';
import { LandingPage } from './LandingPage';

describe('LandingPage', () => {
  it('leads with one primary action to start anonymously', () => {
    renderWithProviders(<LandingPage />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Check in with yourself, privately.' }),
    ).toBeInTheDocument();
    const starts = screen.getAllByRole('link', { name: 'Start anonymously' });
    for (const link of starts) expect(link).toHaveAttribute('href', '/start');
  });

  it('states plainly what the product is not', () => {
    renderWithProviders(<LandingPage />);
    expect(screen.getByText(/A diagnosis\. Scores describe/)).toBeInTheDocument();
    expect(screen.getByText(/A therapist or an emergency service/)).toBeInTheDocument();
  });

  it('offers tap-to-call help lines', () => {
    renderWithProviders(<LandingPage />);
    const help = screen.getByRole('region', { name: 'If you are not safe right now' });
    expect(within(help).getByRole('link', { name: /Tele-MANAS 14416/ })).toHaveAttribute(
      'href',
      'tel:14416',
    );
    expect(within(help).getByRole('link', { name: /Emergency 112/ })).toHaveAttribute(
      'href',
      'tel:112',
    );
  });
});
