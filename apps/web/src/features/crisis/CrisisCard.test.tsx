import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TestProviders } from '../../../tests/render';
import { CrisisCard } from './CrisisCard';

describe('CrisisCard', () => {
  it('shows tap-to-call numbers even when the API is unreachable', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('offline'))),
    );

    render(
      <TestProviders>
        <CrisisCard />
      </TestProviders>,
    );

    expect(screen.getByRole('link', { name: /Call Tele-MANAS now: 14416/ })).toHaveAttribute(
      'href',
      'tel:14416',
    );
    expect(screen.getByRole('link', { name: '1-800-891-4416' })).toHaveAttribute(
      'href',
      'tel:18008914416',
    );
    expect(screen.getByRole('link', { name: /In danger right now\? Call 112/ })).toHaveAttribute(
      'href',
      'tel:112',
    );
  });

  it('includes a trusted-person prompt and a grounding exercise, and never claims confidentiality', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('offline'))),
    );

    const { container } = render(
      <TestProviders>
        <CrisisCard />
      </TestProviders>,
    );

    expect(screen.getByText('Tell someone you trust')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(5);
    expect(container.textContent).not.toMatch(/confidential|anonymous|no police/i);
  });
});
