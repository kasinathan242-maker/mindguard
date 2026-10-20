import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { Button } from '@/components/ui/Button';
import { OnboardingShell } from './OnboardingShell';

export interface OnboardingState {
  ageConfirmed: true;
}

export function AgeGatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <OnboardingShell>
      <p className="text-sm font-semibold text-accent">{t('onboarding.age.title')}</p>
      <h1 className="mt-3 font-display text-[clamp(2rem,6vw,3rem)] leading-[1.08] font-semibold tracking-tight text-balance">
        {t('onboarding.age.question')}
      </h1>
      <p className="mt-5 max-w-[52ch] text-lg leading-relaxed text-ink-soft">
        {t('onboarding.age.why')}
      </p>
      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Button
          arrow
          onClick={() => {
            const state: OnboardingState = { ageConfirmed: true };
            void navigate('/start/consent', { state });
          }}
        >
          {t('onboarding.age.yes')}
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            void navigate('/start/under-18');
          }}
        >
          {t('onboarding.age.no')}
        </Button>
      </div>
    </OnboardingShell>
  );
}
