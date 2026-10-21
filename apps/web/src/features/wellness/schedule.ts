/** Milliseconds from now until the next occurrence of HH:MM. */
export function msUntil(time: string, now: Date): number {
  const [h = 0, m = 0] = time.split(':').map(Number);
  const next = new Date(now);
  next.setHours(h, m, 0, 0);
  if (next.getTime() <= now.getTime()) next.setDate(next.getDate() + 1);
  return next.getTime() - now.getTime();
}
