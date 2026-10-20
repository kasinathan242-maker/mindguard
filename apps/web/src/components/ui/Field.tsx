import { useId, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

interface FieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label: string;
  hint?: string;
  error?: string | null;
}

export function Field({ label, hint, error, className, ...input }: FieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(' ') || undefined;

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          'min-h-12 rounded-2xl bg-surface px-4 text-base text-ink ring-1 ring-line transition-shadow duration-300 ease-out-soft',
          'placeholder:text-ink-muted focus:ring-2 focus:ring-accent focus:outline-none',
          error && 'ring-2 ring-crisis',
        )}
        {...input}
      />
      {hint && (
        <p id={hintId} className="text-sm text-ink-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-sm font-medium text-crisis">
          {error}
        </p>
      )}
    </div>
  );
}
