import { useTranslation } from 'react-i18next';
import { Link } from 'react-router';

export function LogoMark({ className = 'size-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden className={className}>
      <rect width="64" height="64" rx="18" fill="var(--accent)" />
      <circle cx="32" cy="32" r="14" fill="var(--accent-ink)" />
      <circle cx="32" cy="32" r="7" fill="var(--accent)" />
    </svg>
  );
}

export function Logo({ to = '/' }: { to?: string }) {
  const { t } = useTranslation();
  return (
    <Link
      to={to}
      aria-label={t('nav.home')}
      className="inline-flex min-h-11 items-center gap-2.5 rounded-full pr-2 font-display text-lg font-semibold tracking-tight text-ink"
    >
      <LogoMark />
      <span>MindGuard</span>
    </Link>
  );
}
