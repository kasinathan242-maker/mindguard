import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Bezel } from '@/components/ui/Bezel';
import { apiFetch } from '@/lib/api';
import { cn } from '@/lib/cn';

interface Checkin {
  id: string;
  mood: number;
  energy: number;
  created_at: string;
}

const RANGES = [7, 30, 90] as const;

export function MoodChart() {
  const { t, i18n } = useTranslation();
  const [days, setDays] = useState<(typeof RANGES)[number]>(30);
  // Captured once per mount so render stays pure.
  const [now] = useState(() => Date.now());
  const { data } = useQuery({
    queryKey: ['checkins'],
    queryFn: ({ signal }) => apiFetch<Checkin[]>('/checkins', { signal }),
  });

  const cutoff = now - days * 86_400_000;
  const format = new Intl.DateTimeFormat(i18n.language === 'ta' ? 'ta-IN' : 'en-IN', {
    day: 'numeric',
    month: 'short',
  });
  const points = (data ?? [])
    .filter((c) => new Date(c.created_at).getTime() >= cutoff)
    .reverse()
    .map((c) => ({ date: format.format(new Date(c.created_at)), mood: c.mood, energy: c.energy }));
  const weekStart = now - 7 * 86_400_000;
  const daysThisWeek = new Set(
    (data ?? [])
      .filter((c) => new Date(c.created_at).getTime() >= weekStart)
      .map((c) => new Date(c.created_at).toDateString()),
  ).size;
  const average = points.length
    ? (points.reduce((sum, p) => sum + p.mood, 0) / points.length).toFixed(1)
    : null;

  return (
    <Bezel coreClassName="p-6 sm:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-2xl font-semibold tracking-tight">{t('mood.title')}</h2>
        <div
          role="group"
          aria-label={t('mood.range')}
          className="flex gap-1 rounded-full bg-surface-sunk p-1"
        >
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              aria-pressed={days === r}
              onClick={() => {
                setDays(r);
              }}
              className={cn(
                'min-h-9 rounded-full px-3 text-sm font-semibold',
                days === r ? 'bg-surface text-ink shadow-soft' : 'text-ink-muted',
              )}
            >
              {t('mood.days', { count: r })}
            </button>
          ))}
        </div>
      </div>
      {points.length < 2 ? (
        <p className="mt-4 text-ink-muted">{t('mood.empty')}</p>
      ) : (
        <>
          <p className="mt-2 text-sm text-ink-soft">
            {t('mood.summary', { count: points.length, average })}{' '}
            {t('mood.week', { count: daysThisWeek })}
          </p>
          <div className="mt-4 h-56" aria-hidden>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
                <CartesianGrid stroke="var(--line)" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: 'var(--ink-muted)', fontSize: 12 }}
                  minTickGap={24}
                />
                <YAxis
                  domain={[1, 5]}
                  ticks={[1, 2, 3, 4, 5]}
                  tick={{ fill: 'var(--ink-muted)', fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--surface)',
                    border: '1px solid var(--line)',
                    borderRadius: 12,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="mood"
                  name={t('mood.mood')}
                  stroke="var(--accent)"
                  strokeWidth={2.5}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="energy"
                  name={t('mood.energy')}
                  stroke="var(--ink-muted)"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-ink-muted">{t('mood.legend')}</p>
        </>
      )}
    </Bezel>
  );
}
