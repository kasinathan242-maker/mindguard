import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';

export function DataControls() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [step, setStep] = useState<0 | 1 | 2>(0);
  const [error, setError] = useState(false);

  const download = async () => {
    setError(false);
    const response = await fetch('/api/v1/privacy/export', { credentials: 'include' });
    if (!response.ok) {
      setError(true);
      return;
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = 'mindguard-export.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  const remove = async () => {
    setError(false);
    const response = await fetch('/api/v1/privacy/account', {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirm: 'DELETE' }),
    });
    if (!response.ok) {
      setError(true);
      return;
    }
    client.clear();
    client.setQueryData(['session'], null);
    void navigate('/', { replace: true });
  };

  return (
    <Bezel coreClassName="grid gap-5 p-6 sm:p-8">
      <div>
        <h3 className="font-semibold">{t('privacyPage.exportTitle')}</h3>
        <p className="mt-1 text-sm text-ink-soft">{t('privacyPage.exportBody')}</p>
        <Button variant="secondary" className="mt-3" onClick={() => void download()}>
          {t('privacyPage.exportButton')}
        </Button>
      </div>
      <div>
        <h3 className="font-semibold">{t('privacyPage.deleteTitle')}</h3>
        <p className="mt-1 text-sm text-ink-soft">{t('privacyPage.deleteBody')}</p>
        {step === 0 && (
          <Button
            variant="secondary"
            className="mt-3"
            onClick={() => {
              setStep(1);
            }}
          >
            {t('privacyPage.deleteButton')}
          </Button>
        )}
        {step === 1 && (
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setStep(2);
              }}
            >
              {t('privacyPage.deleteConfirm1')}
            </Button>
            <Button
              variant="quiet"
              onClick={() => {
                setStep(0);
              }}
            >
              {t('privacyPage.cancel')}
            </Button>
          </div>
        )}
        {step === 2 && (
          <div
            role="alertdialog"
            aria-label={t('privacyPage.deleteTitle')}
            className="mt-3 grid gap-2"
          >
            <p className="font-medium text-ink">{t('privacyPage.deleteFinalWarning')}</p>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => void remove()}>{t('privacyPage.deleteConfirm2')}</Button>
              <Button
                variant="quiet"
                onClick={() => {
                  setStep(0);
                }}
              >
                {t('privacyPage.cancel')}
              </Button>
            </div>
          </div>
        )}
      </div>
      {error && (
        <p role="alert" className="text-sm font-medium text-crisis">
          {t('errorGeneric')}
        </p>
      )}
    </Bezel>
  );
}
