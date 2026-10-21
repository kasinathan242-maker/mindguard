import { CheckCircleIcon, ShieldCheckIcon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';

export function GrievanceSection() {
  const { t } = useTranslation();

  const rights = t('privacyPage.rightsList', { returnObjects: true }) as string[];

  return (
    <Bezel coreClassName="p-6 sm:p-8">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-accent">
          <ShieldCheckIcon size={24} weight="duotone" aria-hidden />
        </span>
        <div>
          <h3 className="font-display text-xl font-semibold tracking-tight text-ink">
            {t('privacyPage.grievanceTitle')}
          </h3>
          <p className="mt-1 text-sm text-ink-soft">
            {t('privacyPage.grievanceIntro')}
          </p>
        </div>
      </div>

      <div className="mt-6 border-t border-line pt-6">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
          Statutory Rights
        </h4>
        <ul className="mt-3 grid gap-2.5 sm:grid-cols-2">
          {rights.map((right) => (
            <li key={right} className="flex items-start gap-2.5 text-sm text-ink-soft">
              <CheckCircleIcon size={16} weight="fill" className="mt-0.5 shrink-0 text-accent" aria-hidden />
              <span>{right}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 rounded-2xl bg-surface-sunk/60 p-4 sm:p-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium text-ink-muted">
              {t('privacyPage.officerLabel')}
            </p>
            <p className="text-base font-semibold text-ink">
              {t('privacyPage.officerName')}
            </p>
            <p className="text-xs font-medium text-accent">
              {t('privacyPage.officerSla')}
            </p>
          </div>
          <a
            href={`mailto:${t('privacyPage.officerEmail')}`}
            className="inline-flex items-center justify-center rounded-xl bg-surface px-4 py-2 text-sm font-medium text-ink shadow-sm ring-1 ring-line hover:bg-surface-elevated hover:text-accent transition-colors"
          >
            {t('privacyPage.officerEmail')}
          </a>
        </div>
        <p className="mt-3 text-xs text-ink-muted leading-relaxed">
          {t('privacyPage.escalationNote')}
        </p>
      </div>
    </Bezel>
  );
}
