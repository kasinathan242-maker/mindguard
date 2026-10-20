import { useState, type SubmitEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Navigate, useLocation, useNavigate } from 'react-router';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { ConsentRow } from '@/features/privacy/ConsentRow';
import { ApiError } from '@/lib/api';
import type { Locale } from '@/lib/i18n';
import { OPTIONAL_SCOPES, useStartAnonymous, type ConsentScope } from '@/lib/session';
import type { OnboardingState } from './AgeGatePage';
import { OnboardingShell } from './OnboardingShell';

type OptionalScope = Exclude<ConsentScope, 'core'>;

function hasConfirmedAge(state: unknown): state is OnboardingState {
  return typeof state === 'object' && state !== null && 'ageConfirmed' in state;
}

export function ConsentPage() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const start = useStartAnonymous();
  const [core, setCore] = useState(false);
  const [optional, setOptional] = useState<Record<OptionalScope, boolean>>({
    chat_history: false,
    voice: false,
    wearables: false,
    cloud_llm: false,
    reminders: false,
  });
  const [showCoreError, setShowCoreError] = useState(false);

  if (!hasConfirmedAge(location.state)) return <Navigate to="/start" replace />;

  const onSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!core) {
      setShowCoreError(true);
      return;
    }
    const locale: Locale = i18n.language === 'ta' ? 'ta' : 'en';
    start.mutate(
      { locale, consents: { core: true, ...optional } },
      {
        onSuccess: () => {
          void navigate('/app', { replace: true });
        },
      },
    );
  };

  const errorText =
    start.error instanceof ApiError && start.error.status === 429
      ? t('login.tooMany')
      : t('errorGeneric');

  return (
    <OnboardingShell>
      <h1 className="font-display text-[clamp(1.9rem,5.5vw,2.75rem)] leading-[1.1] font-semibold tracking-tight text-balance">
        {t('onboarding.consent.title')}
      </h1>
      <p className="mt-4 max-w-[58ch] text-lg leading-relaxed text-ink-soft">
        {t('onboarding.consent.intro')}
      </p>

      <form onSubmit={onSubmit} noValidate className="mt-10">
        <Bezel coreClassName="divide-y divide-line">
          <ConsentRow
            scope="core"
            required
            checked={core}
            onChange={(checked) => {
              setCore(checked);
              if (checked) setShowCoreError(false);
            }}
          />
          {OPTIONAL_SCOPES.map((scope) => (
            <ConsentRow
              key={scope}
              scope={scope}
              checked={optional[scope]}
              onChange={(checked) => {
                setOptional((current) => ({ ...current, [scope]: checked }));
              }}
            />
          ))}
        </Bezel>

        <div aria-live="polite" className="mt-5 min-h-6 text-sm font-medium text-crisis">
          {showCoreError && t('onboarding.consent.mustAgree')}
          {start.isError && errorText}
        </div>

        <div className="mt-4 flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <Button type="submit" arrow disabled={start.isPending}>
            {t('onboarding.consent.submit')}
          </Button>
          <p className="text-sm text-ink-muted">
            {t('onboarding.consent.haveAccount')}{' '}
            <Link to="/login" className="font-semibold text-ink underline underline-offset-4">
              {t('nav.signIn')}
            </Link>
          </p>
        </div>
      </form>
    </OnboardingShell>
  );
}
