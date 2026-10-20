import { describe, expect, it } from 'vitest';
import en from '@/locales/en/common.json';
import ta from '@/locales/ta/common.json';

function keyPaths(value: unknown, prefix = ''): string[] {
  if (Array.isArray(value)) return [`${prefix}[${value.length}]`];
  if (value && typeof value === 'object') {
    return Object.entries(value).flatMap(([key, child]) =>
      keyPaths(child, prefix ? `${prefix}.${key}` : key),
    );
  }
  return [prefix];
}

function strings(value: unknown): string[] {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(strings);
  if (value && typeof value === 'object') return Object.values(value).flatMap(strings);
  return [];
}

describe('locales', () => {
  it('Tamil has exactly the same keys as English', () => {
    expect(keyPaths(ta).sort()).toEqual(keyPaths(en).sort());
  });

  it('no translation is left empty', () => {
    for (const text of [...strings(en), ...strings(ta)]) expect(text.trim()).not.toBe('');
  });

  it('copy never uses em or en dashes', () => {
    for (const text of [...strings(en), ...strings(ta)]) expect(text).not.toMatch(/[–—]/);
  });

  it('copy avoids stigmatising clinical terms', () => {
    for (const text of strings(en))
      expect(text.toLowerCase()).not.toMatch(/\b(patient|disorder)\b/);
  });
});
