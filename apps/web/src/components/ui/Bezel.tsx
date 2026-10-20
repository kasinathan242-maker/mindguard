import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface BezelProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Classes for the inner core (background, padding). */
  coreClassName?: string;
}

/** Double-bezel container: a tinted outer tray holding an inner plate with concentric corners. */
export function Bezel({ children, className, coreClassName, ...rest }: BezelProps) {
  return (
    <div
      className={cn(
        'rounded-[1.75rem] bg-ink/[0.035] p-1.5 ring-1 ring-line dark:bg-white/[0.03]',
        className,
      )}
      {...rest}
    >
      <div
        className={cn(
          'bezel-highlight h-full rounded-[calc(1.75rem-0.375rem)] bg-surface',
          coreClassName,
        )}
      >
        {children}
      </div>
    </div>
  );
}
