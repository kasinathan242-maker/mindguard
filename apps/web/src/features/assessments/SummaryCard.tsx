import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { apiFetch } from '@/lib/api';

interface Summary {
  latest: { type: string; total: number; max_score: number; band: string }[];
  mood: { checkins: number; average_mood: number | null; average_sleep_hours: number | null };
  next_step: string | null;
  patterns: { metric: string; points: number; correlation: number | null; strength: string }[];
}

export function SummaryCard() {
  const { t, i18n } = useTranslation();
  const [error, setError] = useState(false);
  const { data } = useQuery({
    queryKey: ['summary'],
    queryFn: ({ signal }) => apiFetch<Summary>('/insights/summary', { signal }),
  });

  const download = async () => {
    setError(false);
    const locale = i18n.language === 'ta' ? 'ta' : 'en';
    const response = await fetch(`/api/v1/reports/screening.pdf?locale=${locale}`, { credentials: 'include' });
    if (!response.ok) {
      setError(true);
      return;
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = `mindguard-screening-summary-${locale}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!data) return null;
  return (
    <Bezel coreClassName="grid gap-4 p-6 sm:p-8">
      <h2 className="font-display text-2xl font-semibold tracking-tight">{t('summary.title')}</h2>
      <div className="grid gap-4 sm:grid-cols-3">
        <section>
          <h3 className="text-sm font-semibold text-accent">{t('summary.scores')}</h3>
          {data.latest.length === 0 ? (
            <p className="mt-1 text-sm text-ink-muted">{t('assessments.neverTaken')}</p>
          ) : (
            <ul className="mt-1 text-sm text-ink-soft">
              {data.latest.map((s) => (
                <li key={s.type}>
                  {t(`assessments.instruments.${s.type}.name`)}: {s.total}/{s.max_score},{' '}
                  {t(`assessments.bands.${s.band}.label`)}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h3 className="text-sm font-semibold text-accent">{t('summary.selfReport')}</h3>
          <p className="mt-1 text-sm text-ink-soft">
            {t('summary.checkins', {
              count: data.mood.checkins,
              mood: data.mood.average_mood ?? '-',
            })}
          </p>
        </section>
        <section>
          <h3 className="text-sm font-semibold text-accent">{t('summary.diagnosis')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{t('summary.noDiagnosis')}</p>
        </section>
      </div>
      <section aria-labelledby="patterns-title">
        <h3 id="patterns-title" className="text-sm font-semibold text-accent">
          {t('summary.patternsTitle')}
        </h3>
        <ul className="mt-1 grid gap-1 text-sm text-ink-soft">
          {data.patterns.map((p) => (
            <li key={p.metric}>
              {p.correlation === null
                ? t('summary.patternNeedsData', {
                    metric: t(`summary.metrics.${p.metric}`),
                    count: p.points,
                  })
                : t(p.correlation >= 0 ? 'summary.patternUp' : 'summary.patternDown', {
                    metric: t(`summary.metrics.${p.metric}`),
                    strength: t(`summary.strength.${p.strength}`),
                  })}
            </li>
          ))}
        </ul>
        <p className="mt-1 text-xs text-ink-muted">{t('summary.patternNote')}</p>
      </section>
      <p className="text-sm font-medium text-ink">{t('assessments.result.notDiagnosis')}</p>
      <Button variant="secondary" className="justify-self-start" onClick={() => void download()}>
        {t('summary.download')}
      </Button>
      {error && (
        <p role="alert" className="text-sm font-medium text-crisis">
          {t('errorGeneric')}
        </p>
      )}
    </Bezel>
  );
}
