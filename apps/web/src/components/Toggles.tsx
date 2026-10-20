import { MoonIcon, SunIcon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { setLocale, type Locale } from '@/lib/i18n';
import { isDarkNow, useTheme } from '@/lib/theme';

const LABELS: Record<Locale, { short: string; name: string }> = {
  en: { short: 'EN', name: 'English' },
  ta: { short: 'த', name: 'தமிழ்' },
};

interface LanguageToggleProps {
  /** Called after the UI language changes, e.g. to persist it to the account. */
  onChange?: (locale: Locale) => void;
}

export function LanguageToggle({ onChange }: LanguageToggleProps) {
  const { t, i18n } = useTranslation();
  const current: Locale = i18n.language === 'ta' ? 'ta' : 'en';

  return (
    <div
      role="group"
      aria-label={t('nav.language')}
      className="inline-flex rounded-full bg-surface-sunk p-1 ring-1 ring-line"
    >
      {(Object.keys(LABELS) as Locale[]).map((locale) => (
        <button
          key={locale}
          type="button"
          lang={locale}
          aria-pressed={current === locale}
          onClick={() => {
            setLocale(locale);
            onChange?.(locale);
          }}
          className={
            'min-h-9 min-w-10 rounded-full px-3 text-sm font-semibold transition-colors duration-300 ease-out-soft ' +
            (current === locale
              ? 'bg-surface text-ink shadow-soft'
              : 'text-ink-muted hover:text-ink')
          }
        >
          {LABELS[locale].short}
          <span className="sr-only"> ({LABELS[locale].name})</span>
        </button>
      ))}
    </div>
  );
}

export function ThemeToggle() {
  const { t } = useTranslation();
  const { preference, toggle } = useTheme();
  const dark = isDarkNow(preference);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? t('nav.themeLight') : t('nav.themeDark')}
      className="inline-flex size-11 items-center justify-center rounded-full text-ink-soft ring-1 ring-line transition-colors duration-300 ease-out-soft hover:bg-surface-sunk hover:text-ink"
    >
      {dark ? <SunIcon size={18} weight="light" /> : <MoonIcon size={18} weight="light" />}
    </button>
  );
}
