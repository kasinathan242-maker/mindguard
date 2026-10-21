import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/Button';
import { useConsents } from '@/lib/session';
import { msUntil } from './schedule';

const STORAGE_KEY = 'mindguard.reminder';

function readTime(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

async function triggerNotification(title: string, options: NotificationOptions): Promise<void> {
  if ('serviceWorker' in navigator) {
    try {
      const reg = await navigator.serviceWorker.ready;
      if (typeof reg.showNotification === 'function') {
        await reg.showNotification(title, options);
        return;
      }
    } catch {
      // Fallback to window Notification constructor
    }
  }
  try {
    new Notification(title, options);
  } catch {
    // Blocked or mobile browser requiring ServiceWorker
  }
}

/**
 * A gentle daily reminder while MindGuard is open (tab or installed app). The time stays on
 * this device; nothing is sent to the server. Background push needs a push service and is not
 * built yet.
 */
export function Reminders() {
  const { t } = useTranslation();
  const consents = useConsents();
  const [time, setTime] = useState<string | null>(readTime);
  const [draft, setDraft] = useState(time ?? '20:00');
  const granted = consents.data?.items.find((c) => c.scope === 'reminders')?.granted ?? false;
  const supported = typeof Notification !== 'undefined';

  useEffect(() => {
    if (!granted || !time || !supported || Notification.permission !== 'granted') return;
    const id = window.setTimeout(
      () => {
        void triggerNotification(t('reminders.notificationTitle'), {
          body: t('reminders.notificationBody'),
          icon: '/favicon.ico',
        });
      },
      msUntil(time, new Date()),
    );
    return () => {
      window.clearTimeout(id);
    };
  }, [granted, time, supported, t]);

  if (!granted) return <p className="text-sm text-ink-muted">{t('reminders.needsConsent')}</p>;
  if (!supported) return <p className="text-sm text-ink-muted">{t('reminders.unsupported')}</p>;

  const save = async () => {
    if ((await Notification.requestPermission()) !== 'granted') return;
    try {
      localStorage.setItem(STORAGE_KEY, draft);
    } catch {
      // Kept for this visit only.
    }
    setTime(draft);
  };

  return (
    <div className="grid gap-3">
      <label htmlFor="reminder-time" className="text-sm font-medium text-ink">
        {t('reminders.label')}
      </label>
      <div className="flex flex-wrap gap-2">
        <input
          id="reminder-time"
          type="time"
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
          }}
          className="min-h-11 rounded-2xl bg-surface px-4 ring-1 ring-line focus:ring-2 focus:ring-accent focus:outline-none"
        />
        <Button variant="secondary" onClick={() => void save()}>
          {t('reminders.save')}
        </Button>
        {time && (
          <Button
            variant="quiet"
            onClick={() => {
              try {
                localStorage.removeItem(STORAGE_KEY);
              } catch {
                // Nothing stored.
              }
              setTime(null);
            }}
          >
            {t('reminders.off')}
          </Button>
        )}
      </div>
      <p role="status" className="text-sm text-ink-soft">
        {time ? t('reminders.set', { time }) : t('reminders.none')}
      </p>
      <p className="text-xs text-ink-muted">{t('reminders.note')}</p>
    </div>
  );
}
