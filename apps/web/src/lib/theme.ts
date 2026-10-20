import { useCallback, useSyncExternalStore } from 'react';

export type ThemePreference = 'system' | 'light' | 'dark';

const STORAGE_KEY = 'mindguard.theme';
const listeners = new Set<() => void>();

function read(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'light' || stored === 'dark' ? stored : 'system';
  } catch {
    return 'system';
  }
}

function apply(preference: ThemePreference): void {
  const root = document.documentElement;
  if (preference === 'system') delete root.dataset.theme;
  else root.dataset.theme = preference;
}

export function setTheme(preference: ThemePreference): void {
  try {
    if (preference === 'system') localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, preference);
  } catch {
    // Not persisted; still applied for this visit.
  }
  apply(preference);
  listeners.forEach((notify) => {
    notify();
  });
}

function subscribe(notify: () => void): () => void {
  listeners.add(notify);
  return () => listeners.delete(notify);
}

/** Whether the page currently renders dark, resolving `system` against the OS setting. */
export function isDarkNow(preference: ThemePreference): boolean {
  if (preference !== 'system') return preference === 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function useTheme() {
  const preference = useSyncExternalStore(subscribe, read, () => 'system' as const);
  const toggle = useCallback(() => {
    setTheme(isDarkNow(preference) ? 'light' : 'dark');
  }, [preference]);
  return { preference, toggle };
}
