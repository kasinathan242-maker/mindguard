export type BreathPhase = 'in' | 'holdFull' | 'out' | 'holdEmpty';
export type BreathPattern = 'box' | '478';

/** Phases and their lengths in seconds. */
export const PATTERNS: Record<BreathPattern, [BreathPhase, number][]> = {
  box: [
    ['in', 4],
    ['holdFull', 4],
    ['out', 4],
    ['holdEmpty', 4],
  ],
  '478': [
    ['in', 4],
    ['holdFull', 7],
    ['out', 8],
  ],
};
