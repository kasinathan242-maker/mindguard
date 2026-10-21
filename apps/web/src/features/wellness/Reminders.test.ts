import { describe, expect, it } from 'vitest';
import { msUntil } from './schedule';

describe('msUntil', () => {
  it('schedules later today, or tomorrow once the time has passed', () => {
    const now = new Date(2026, 9, 21, 19, 0, 0);
    expect(msUntil('20:30', now)).toBe(90 * 60 * 1000);
    expect(msUntil('08:00', now)).toBe(13 * 60 * 60 * 1000);
    expect(msUntil('19:00', now)).toBe(24 * 60 * 60 * 1000);
  });
});
