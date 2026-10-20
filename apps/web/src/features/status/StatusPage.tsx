import { useTranslation } from 'react-i18next';
import { useHealth } from './useHealth';

export function StatusPage() {
  const { t } = useTranslation();
  const { data, isPending, isError } = useHealth();

  let headline: string;
  if (isPending) headline = t('status.checking');
  else if (isError) headline = t('status.unreachable');
  else headline = data.status === 'ok' ? t('status.ok') : t('status.degraded');

  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-6 px-6 py-16">
      <p className="text-sm tracking-wide text-ink-muted uppercase">{t('appName')}</p>
      <h1 className="font-display text-4xl leading-tight text-ink">{t('status.title')}</h1>
      <p role="status" aria-live="polite" className="text-lg text-ink-soft">
        {headline}
      </p>
      {data && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-ink-soft">
          <dt>{t('status.database')}</dt>
          <dd>{data.checks.database}</dd>
          <dt>{t('status.redis')}</dt>
          <dd>{data.checks.redis}</dd>
          <dt className="sr-only">version</dt>
          <dd className="col-span-2 pt-2 text-sm text-ink-muted">
            {t('status.version', { version: data.version })}
          </dd>
        </dl>
      )}
    </main>
  );
}
