import { LifebuoyIcon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import { useCrisis } from './context';

interface NeedHelpButtonProps {
  className?: string;
  /** Show only the icon below the `sm` breakpoint (the label stays available to screen readers). */
  compact?: boolean;
}

export function NeedHelpButton({ className, compact = false }: NeedHelpButtonProps) {
  const { t } = useTranslation();
  const { openCrisis } = useCrisis();
  return (
    <button
      type="button"
      onClick={openCrisis}
      className={cn(
        // Calm styling on purpose: alarm red is reserved for the inside of the crisis card.
        'inline-flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-full bg-accent-soft px-4 text-sm font-semibold text-accent transition-transform duration-500 ease-spring active:scale-[0.98]',
        className,
      )}
    >
      <LifebuoyIcon size={18} weight="bold" aria-hidden />
      <span className={compact ? 'sr-only sm:not-sr-only' : undefined}>{t('crisis.needHelp')}</span>
    </button>
  );
}
