import { PhoneIcon, UsersThreeIcon, WarningCircleIcon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { ButtonLink } from '@/components/ui/Button';
import { OnboardingShell } from './OnboardingShell';

export function Under18Page() {
  const { t } = useTranslation();
  return (
    <OnboardingShell>
      <h1 className="font-display text-[clamp(2rem,6vw,3rem)] leading-[1.08] font-semibold tracking-tight">
        {t('onboarding.under18.title')}
      </h1>
      <p className="mt-5 max-w-[56ch] text-lg leading-relaxed text-ink-soft">
        {t('onboarding.under18.body')}
      </p>

      <Bezel className="mt-10" coreClassName="divide-y divide-line">
        <a
          href="tel:14416"
          className="flex items-start gap-4 p-6 transition-colors duration-300 ease-out-soft hover:bg-surface-sunk sm:p-7"
        >
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-accent text-accent-ink">
            <PhoneIcon size={20} weight="fill" aria-hidden />
          </span>
          <span>
            <span className="block font-display text-xl font-semibold">Tele-MANAS 14416</span>
            <span className="mt-1 block text-ink-soft">{t('onboarding.under18.telemanas')}</span>
            <span className="mt-1 block text-sm text-ink-muted tabular-nums">1-800-891-4416</span>
          </span>
        </a>
        <div className="flex items-start gap-4 p-6 sm:p-7">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent">
            <UsersThreeIcon size={20} weight="light" aria-hidden />
          </span>
          <p className="pt-2 text-ink-soft">{t('onboarding.under18.trusted')}</p>
        </div>
        <a
          href="tel:112"
          className="flex items-start gap-4 p-6 transition-colors duration-300 ease-out-soft hover:bg-surface-sunk sm:p-7"
        >
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-surface-sunk text-ink">
            <WarningCircleIcon size={20} weight="light" aria-hidden />
          </span>
          <p className="pt-2 font-medium text-ink">{t('onboarding.under18.emergency')}</p>
        </a>
      </Bezel>

      <ButtonLink to="/" variant="secondary" className="mt-10">
        {t('onboarding.under18.back')}
      </ButtonLink>
    </OnboardingShell>
  );
}
