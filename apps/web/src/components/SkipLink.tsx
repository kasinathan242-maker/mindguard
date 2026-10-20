import { useTranslation } from 'react-i18next';

export const MAIN_ID = 'main';

export function SkipLink() {
  const { t } = useTranslation();
  return (
    <a
      href={`#${MAIN_ID}`}
      className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-surface focus:px-5 focus:py-3 focus:text-ink focus:shadow-soft"
    >
      {t('nav.skip')}
    </a>
  );
}
