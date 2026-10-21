import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Bezel } from '@/components/ui/Bezel';
import { cn } from '@/lib/cn';
import type { AssessmentResult, InstrumentType } from './api';

interface ScoreChartProps {
  results: AssessmentResult[];
}

type FilterType = 'ALL' | InstrumentType;

export function ScoreChart({ results }: ScoreChartProps) {
  const { t, i18n } = useTranslation();
  const [filter, setFilter] = useState<FilterType>('ALL');

  const formatter = new Intl.DateTimeFormat(i18n.language === 'ta' ? 'ta-IN' : 'en-IN', {
    day: 'numeric',
    month: 'short',
  });

  const sorted = [...results].reverse();
  const filtered = filter === 'ALL' ? sorted : sorted.filter((r) => r.type === filter);

  if (filtered.length < 2) return null;

  const data = filtered.map((r) => ({
    date: formatter.format(new Date(r.created_at)),
    timestamp: new Date(r.created_at).getTime(),
    score: r.total,
    type: r.type,
    band: t(`assessments.bands.${r.severity_band}.label`),
    phq9: r.type === 'PHQ9' ? r.total : undefined,
    gad7: r.type === 'GAD7' ? r.total : undefined,
  }));

  const maxScore = filter === 'GAD7' ? 21 : 27;

  return (
    <Bezel coreClassName="p-6 sm:p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-semibold tracking-tight">
            {t('assessments.chartTitle', { defaultValue: 'Score Trends' })}
          </h2>
          <p className="mt-1 text-sm text-ink-soft">
            {t('assessments.chartSubtitle', {
              defaultValue: 'How your screening scores have shifted across past self-checks.',
            })}
          </p>
        </div>
        <div
          role="group"
          aria-label={t('assessments.filter', { defaultValue: 'Filter check type' })}
          className="flex gap-1 rounded-full bg-surface-sunk p-1"
        >
          {(['ALL', 'PHQ9', 'GAD7'] as const).map((type) => (
            <button
              key={type}
              type="button"
              aria-pressed={filter === type}
              onClick={() => {
                setFilter(type);
              }}
              className={cn(
                'min-h-9 rounded-full px-3 text-sm font-semibold transition-colors',
                filter === type ? 'bg-surface text-ink shadow-soft' : 'text-ink-muted hover:text-ink',
              )}
            >
              {type === 'ALL'
                ? t('assessments.filterAll', { defaultValue: 'All' })
                : t(`assessments.instruments.${type}.name`)}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 h-64" aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 12, right: 12, bottom: 0, left: -20 }}>
            <CartesianGrid stroke="var(--line)" vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fill: 'var(--ink-muted)', fontSize: 12 }}
              minTickGap={20}
            />
            <YAxis
              domain={[0, maxScore]}
              tick={{ fill: 'var(--ink-muted)', fontSize: 12 }}
              allowDecimals={false}
            />
            <Tooltip
              content={({ active, payload }) => {
                const item = payload[0];
                if (!active || !item) return null;
                const point = item.payload as (typeof data)[number];
                return (
                  <div className="rounded-xl border border-line bg-surface p-3 shadow-lg">
                    <p className="text-xs font-semibold text-ink-muted">{point.date}</p>
                    <p className="mt-1 text-sm font-bold text-ink">
                      {t(`assessments.instruments.${point.type}.name`)}: {point.score}
                    </p>
                    <p className="text-xs text-accent">{point.band}</p>
                  </div>
                );
              }}
            />
            {filter !== 'GAD7' && (
              <Line
                type="monotone"
                dataKey="phq9"
                name={t('assessments.instruments.PHQ9.name')}
                stroke="var(--accent)"
                strokeWidth={2.5}
                dot={{ r: 4, fill: 'var(--accent)' }}
                activeDot={{ r: 6 }}
                connectNulls
              />
            )}
            {filter !== 'PHQ9' && (
              <Line
                type="monotone"
                dataKey="gad7"
                name={t('assessments.instruments.GAD7.name')}
                stroke="#4a7c82"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#4a7c82' }}
                activeDot={{ r: 6 }}
                connectNulls
              />
            )}
            <ReferenceLine y={10} stroke="#d97706" strokeDasharray="4 4" label={{ value: 'Moderate (10)', fill: '#d97706', fontSize: 11 }} />
            {filter === 'ALL' && <Legend />}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="sr-only">
        {t('assessments.chartA11y', {
          count: filtered.length,
          defaultValue: 'Screening history chart showing {{count}} past assessments.',
        })}
      </p>
    </Bezel>
  );
}
