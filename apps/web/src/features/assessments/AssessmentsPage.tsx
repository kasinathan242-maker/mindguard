import { ClipboardTextIcon, WavesIcon, type Icon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { ButtonLink } from '@/components/ui/Button';
import { Reveal } from '@/components/ui/Reveal';
import { ScoreChart } from './ScoreChart';
import { SummaryCard } from './SummaryCard';
import { useAssessmentHistory, type AssessmentResult, type InstrumentType } from './api';

const CARDS: { type: InstrumentType; icon: Icon; tone: string }[] = [
  { type: 'PHQ9', icon: ClipboardTextIcon, tone: 'bg-surface' },
  { type: 'GAD7', icon: WavesIcon, tone: 'bg-accent-soft' },
];

function useDateFormat() {
  const { i18n } = useTranslation();
  const formatter = new Intl.DateTimeFormat(i18n.language === 'ta' ? 'ta-IN' : 'en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
  return (iso: string) => formatter.format(new Date(iso));
}

function LastResult({ result }: { result: AssessmentResult | undefined }) {
  const { t } = useTranslation();
  const formatDate = useDateFormat();
  if (!result) return <p className="text-sm text-ink-muted">{t('assessments.neverTaken')}</p>;
  return (
    <p className="text-sm text-ink-soft">
      {t('assessments.lastResult', {
        date: formatDate(result.created_at),
        total: result.total,
        max: result.max_score,
        band: t(`assessments.bands.${result.severity_band}.label`),
      })}
    </p>
  );
}

function History({ results }: { results: AssessmentResult[] }) {
  const { t } = useTranslation();
  const formatDate = useDateFormat();
  if (results.length === 0) {
    return (
      <Bezel coreClassName="p-7 text-center">
        <p className="font-display text-xl font-semibold">{t('assessments.historyEmptyTitle')}</p>
        <p className="mt-2 text-ink-soft">{t('assessments.historyEmptyBody')}</p>
      </Bezel>
    );
  }
  return (
    <Bezel coreClassName="divide-y divide-line">
      {results.slice(0, 12).map((result) => (
        <div
          key={result.id}
          className="flex flex-wrap items-center justify-between gap-3 px-6 py-4"
        >
          <div>
            <p className="font-semibold text-ink">
              {t(`assessments.instruments.${result.type}.name`)}
            </p>
            <p className="text-sm text-ink-muted">{formatDate(result.created_at)}</p>
          </div>
          <p className="text-right">
            <span className="font-display text-xl font-semibold tabular-nums">{result.total}</span>
            <span className="text-sm text-ink-muted tabular-nums"> / {result.max_score}</span>
            <span className="block text-sm text-ink-soft">
              {t(`assessments.bands.${result.severity_band}.label`)}
            </span>
          </p>
        </div>
      ))}
    </Bezel>
  );
}

export function AssessmentsPage() {
  const { t } = useTranslation();
  const history = useAssessmentHistory();
  const results = history.data ?? [];

  return (
    <div className="grid gap-12">
      <Reveal>
        <h1 className="font-display text-[clamp(2rem,5vw,3rem)] leading-[1.08] font-semibold tracking-tight">
          {t('assessments.title')}
        </h1>
        <p className="mt-3 max-w-[58ch] text-lg leading-relaxed text-ink-soft">
          {t('assessments.intro')}
        </p>
      </Reveal>

      <div className="grid gap-4 md:grid-cols-2">
        {CARDS.map(({ type, icon: CardIcon, tone }, index) => (
          <Reveal key={type} delay={index * 0.08}>
            <Bezel coreClassName={`flex h-full flex-col gap-5 p-7 sm:p-8 ${tone}`}>
              <CardIcon size={30} weight="light" className="text-accent" aria-hidden />
              <div>
                <h2 className="font-display text-2xl font-semibold tracking-tight">
                  {t(`assessments.instruments.${type}.name`)}
                </h2>
                <p className="mt-2 leading-relaxed text-ink-soft">
                  {t(`assessments.instruments.${type}.about`)}
                </p>
              </div>
              {history.isPending ? (
                <div className="h-5 w-48 animate-pulse rounded-full bg-surface-sunk" aria-hidden />
              ) : (
                <LastResult result={results.find((r) => r.type === type)} />
              )}
              <ButtonLink to={`/app/assessments/${type}`} arrow className="mt-auto self-start">
                {t('assessments.start')}
              </ButtonLink>
            </Bezel>
          </Reveal>
        ))}
      </div>

      <SummaryCard />

      <section aria-labelledby="history-title" className="grid gap-6">
        <h2 id="history-title" className="font-display text-2xl font-semibold tracking-tight">
          {t('assessments.historyTitle')}
        </h2>
        {history.isError ? (
          <p className="text-crisis">{t('errorGeneric')}</p>
        ) : (
          <>
            <ScoreChart results={results} />
            <History results={results} />
          </>
        )}
      </section>
    </div>
  );
}

