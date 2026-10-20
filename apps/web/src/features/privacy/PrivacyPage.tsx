import { CheckCircleIcon } from '@phosphor-icons/react';
import { useEffect, useState, type SubmitEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { ApiError } from '@/lib/api';
import { useConsents, useSession, useUpdateConsents, useUpgrade } from '@/lib/session';
import { ConsentRow } from './ConsentRow';
import { DataControls } from './DataControls';
import { WearableImport } from './WearableImport';

function ConsentsSection() {
  const { t } = useTranslation();
  const consents = useConsents();
  const update = useUpdateConsents();
  const [savedScope, setSavedScope] = useState<string | null>(null);

  if (consents.isPending) {
    return <div className="h-96 animate-pulse rounded-[1.75rem] bg-surface-sunk" aria-hidden />;
  }
  if (consents.isError) {
    return <p className="text-crisis">{t('errorGeneric')}</p>;
  }

  return (
    <>
      <Bezel coreClassName="divide-y divide-line">
        {consents.data.items.map((item) => (
          <ConsentRow
            key={item.scope}
            scope={item.scope}
            checked={item.granted}
            required={item.required}
            disabled={item.required || update.isPending}
            onChange={(granted) => {
              setSavedScope(null);
              update.mutate(
                { [item.scope]: granted },
                {
                  onSuccess: () => {
                    setSavedScope(item.scope);
                  },
                },
              );
            }}
          />
        ))}
      </Bezel>
      <p aria-live="polite" className="mt-3 min-h-6 text-sm font-medium">
        {update.isError && <span className="text-crisis">{t('privacyPage.saveError')}</span>}
        {savedScope && !update.isError && (
          <span className="inline-flex items-center gap-1.5 text-accent">
            <CheckCircleIcon size={16} weight="fill" aria-hidden />
            {t('privacyPage.saved')}
          </span>
        )}
      </p>
    </>
  );
}

function AccountSection() {
  const { t } = useTranslation();
  const { data: user } = useSession();
  const upgrade = useUpgrade();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (!user) return null;

  if (!user.is_anonymous) {
    return (
      <Bezel coreClassName="p-6 sm:p-8">
        <p className="text-ink-soft">{t('privacyPage.signedInAs', { email: user.email })}</p>
        {upgrade.isSuccess && (
          <p role="status" className="mt-3 flex items-center gap-2 font-medium text-accent">
            <CheckCircleIcon size={18} weight="fill" aria-hidden />
            {t('privacyPage.upgraded', { email: user.email })}
          </p>
        )}
      </Bezel>
    );
  }

  const onSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    upgrade.mutate({ email, password });
  };

  let error: string | null = null;
  if (upgrade.error instanceof ApiError) {
    if (upgrade.error.status === 409) error = t('privacyPage.emailTaken');
    else if (upgrade.error.status === 422) error = t('privacyPage.invalid');
    else if (upgrade.error.status === 429) error = t('login.tooMany');
    else error = t('errorGeneric');
  } else if (upgrade.error) {
    error = t('errorGeneric');
  }

  return (
    <Bezel coreClassName="p-6 sm:p-8">
      <p className="text-sm font-semibold text-accent">{t('privacyPage.anonymous')}</p>
      <p className="mt-2 max-w-[56ch] leading-relaxed text-ink-soft">
        {t('privacyPage.upgradeIntro')}
      </p>
      <form onSubmit={onSubmit} className="mt-6 grid gap-5 sm:max-w-md">
        <Field
          label={t('privacyPage.email')}
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
          }}
        />
        <Field
          label={t('privacyPage.password')}
          type="password"
          autoComplete="new-password"
          required
          minLength={10}
          hint={t('privacyPage.passwordHint')}
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
          }}
        />
        <p aria-live="polite" className="min-h-5 text-sm font-medium text-crisis">
          {error}
        </p>
        <Button type="submit" disabled={upgrade.isPending} className="justify-self-start">
          {t('privacyPage.upgradeSubmit')}
        </Button>
      </form>
    </Bezel>
  );
}

export function PrivacyPage() {
  const { t } = useTranslation();
  const { hash } = useLocation();

  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
  }, [hash]);

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-[clamp(2rem,5vw,3rem)] leading-[1.08] font-semibold tracking-tight">
        {t('privacyPage.title')}
      </h1>
      <p className="mt-3 max-w-[56ch] text-lg leading-relaxed text-ink-soft">
        {t('privacyPage.intro')}
      </p>

      <section aria-labelledby="consents-title" className="mt-12">
        <h2 id="consents-title" className="mb-5 font-display text-2xl font-semibold tracking-tight">
          {t('privacyPage.consentsTitle')}
        </h2>
        <ConsentsSection />
      </section>

      <section id="account" aria-labelledby="account-title" className="mt-12 scroll-mt-24">
        <h2 id="account-title" className="mb-5 font-display text-2xl font-semibold tracking-tight">
          {t('privacyPage.accountTitle')}
        </h2>
        <AccountSection />
      </section>

      <section aria-labelledby="wearables-title" className="mt-12">
        <h2
          id="wearables-title"
          className="mb-5 font-display text-2xl font-semibold tracking-tight"
        >
          {t('wearables.title')}
        </h2>
        <WearableImport />
      </section>

      <section aria-labelledby="data-title" className="mt-12">
        <h2 id="data-title" className="mb-5 font-display text-2xl font-semibold tracking-tight">
          {t('privacyPage.dataTitle')}
        </h2>
        <DataControls />
      </section>
    </div>
  );
}
