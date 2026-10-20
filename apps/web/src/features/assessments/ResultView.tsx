import { CompassIcon, InfoIcon } from '@phosphor-icons/react';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { ButtonLink } from '@/components/ui/Button';
import { CrisisCard } from '@/features/crisis/CrisisCard';
import type { AssessmentResult } from './api';

export function ResultView({ result }: { result: AssessmentResult }) {
  const { t } = useTranslation();
  const heading = useRef<HTMLHeadingElement>(null);
  const share = result.total / result.max_score;

  useEffect(() => {
    heading.current?.focus();
  }, []);

  return (
    <div className="mx-auto grid max-w-2xl gap-6">
      {result.safety_item_positive && (
        <section aria-label={t('assessments.result.safetyLabel')} className="grid gap-4">
          <p className="rounded-[1.25rem] bg-surface-sunk p-5 leading-relaxed text-ink">
            {t('assessments.result.safetyNote')}
          </p>
          <CrisisCard headingId="result-crisis-title" />
        </section>
      )}

      <Bezel coreClassName="p-7 sm:p-9">
        <p className="text-sm font-semibold text-accent">
          {t(`assessments.instruments.${result.type}.name`)}
        </p>
        <h2
          ref={heading}
          tabIndex={-1}
          className="mt-3 font-display text-[clamp(2rem,6vw,3rem)] leading-[1.05] font-semibold tracking-tight outline-none"
        >
          {t('assessments.result.headline', {
            band: t(`assessments.bands.${result.severity_band}.label`),
          })}
        </h2>
        <p className="mt-4 flex items-baseline gap-2 text-ink-soft">
          <span className="font-display text-4xl font-semibold text-ink tabular-nums">
            {result.total}
          </span>
          <span className="tabular-nums">
            {t('assessments.result.outOf', { max: result.max_score })}
          </span>
        </p>
        <div aria-hidden className="mt-5 h-2 overflow-hidden rounded-full bg-surface-sunk">
          <div
            className="h-full origin-left rounded-full bg-accent"
            style={{ transform: `scaleX(${Math.max(share, 0.02)})` }}
          />
        </div>
        <p className="mt-6 max-w-[56ch] leading-relaxed text-ink-soft">
          {t(`assessments.instruments.${result.type}.focus`)}{' '}
          {t(`assessments.bands.${result.severity_band}.meaning`)}
        </p>
        <p className="mt-6 flex items-start gap-2 text-sm font-medium text-ink">
          <InfoIcon size={18} weight="bold" className="mt-0.5 shrink-0 text-accent" aria-hidden />
          {t('assessments.result.notDiagnosis')}
        </p>
      </Bezel>

      <Bezel coreClassName="bg-accent-soft p-7 sm:p-9">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-full bg-surface text-accent">
            <CompassIcon size={20} weight="light" aria-hidden />
          </span>
          <h3 className="font-display text-2xl font-semibold tracking-tight">
            {t(`assessments.nextSteps.${result.next_step}.title`)}
          </h3>
        </div>
        <p className="mt-4 max-w-[56ch] leading-relaxed text-ink-soft">
          {t(`assessments.nextSteps.${result.next_step}.body`)}
        </p>
      </Bezel>

      <div className="flex flex-wrap gap-3">
        <ButtonLink to="/app/assessments" variant="secondary">
          {t('assessments.result.backToChecks')}
        </ButtonLink>
      </div>
    </div>
  );
}
