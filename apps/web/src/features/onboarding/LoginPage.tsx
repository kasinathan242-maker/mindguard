import { useState, type SubmitEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { ApiError } from '@/lib/api';
import { setLocale } from '@/lib/i18n';
import { useLogin } from '@/lib/session';
import { OnboardingShell } from './OnboardingShell';

export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const login = useLogin();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const onSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    login.mutate(
      { email, password },
      {
        onSuccess: (user) => {
          setLocale(user.locale);
          void navigate('/app', { replace: true });
        },
      },
    );
  };

  let error: string | null = null;
  if (login.error instanceof ApiError) {
    if (login.error.status === 429) error = t('login.tooMany');
    else if (login.error.status === 401 || login.error.status === 422) error = t('login.failed');
    else error = t('errorGeneric');
  } else if (login.error) {
    error = t('errorGeneric');
  }

  return (
    <OnboardingShell>
      <div className="mx-auto w-full max-w-md">
        <h1 className="font-display text-4xl font-semibold tracking-tight">{t('login.title')}</h1>
        <Bezel className="mt-8" coreClassName="p-6 sm:p-8">
          <form onSubmit={onSubmit} className="flex flex-col gap-5">
            <Field
              label={t('login.email')}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
              }}
            />
            <Field
              label={t('login.password')}
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
            />
            <p aria-live="polite" className="min-h-5 text-sm font-medium text-crisis">
              {error}
            </p>
            <Button type="submit" disabled={login.isPending} className="w-full">
              {t('login.submit')}
            </Button>
          </form>
        </Bezel>
        <p className="mt-6 text-center text-sm text-ink-muted">
          {t('login.newHere')}{' '}
          <Link to="/start" className="font-semibold text-ink underline underline-offset-4">
            {t('login.start')}
          </Link>
        </p>
      </div>
    </OnboardingShell>
  );
}
