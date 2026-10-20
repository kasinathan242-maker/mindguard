import { useState, type ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { useConsents } from '@/lib/session';

export function WearableImport() {
  const { t } = useTranslation();
  const consents = useConsents();
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const granted = consents.data?.items.find((c) => c.scope === 'wearables')?.granted ?? false;

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    const response = await fetch('/api/v1/integrations/wearables/import', {
      method: 'POST',
      credentials: 'include',
      body: form,
    });
    const body = (await response.json().catch(() => ({}))) as { days?: number; detail?: unknown };
    setStatus(
      response.ok
        ? { ok: true, text: t('wearables.imported', { count: body.days ?? 0 }) }
        : {
            ok: false,
            text: typeof body.detail === 'string' ? body.detail : t('errorGeneric'),
          },
    );
    event.target.value = '';
  };

  return (
    <Bezel coreClassName="grid gap-3 p-6 sm:p-8">
      <p className="text-sm text-ink-soft">{t('wearables.intro')}</p>
      {granted ? (
        <>
          <label htmlFor="wearables-file" className="text-sm font-medium text-ink">
            {t('wearables.label')}
          </label>
          <input
            id="wearables-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => void upload(e)}
            className="text-sm text-ink-soft file:mr-3 file:min-h-11 file:rounded-full file:border-0 file:bg-accent-soft file:px-4 file:font-semibold file:text-accent"
          />
          <p className="text-xs text-ink-muted">{t('wearables.format')}</p>
        </>
      ) : (
        <p className="text-sm text-ink-muted">{t('wearables.needsConsent')}</p>
      )}
      {status && (
        <p role="status" className={status.ok ? 'text-sm text-accent' : 'text-sm text-crisis'}>
          {status.text}
        </p>
      )}
    </Bezel>
  );
}
