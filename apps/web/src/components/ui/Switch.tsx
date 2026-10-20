import { cn } from '@/lib/cn';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  labelledBy: string;
  describedBy?: string;
  disabled?: boolean;
}

export function Switch({ checked, onChange, labelledBy, describedBy, disabled }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-labelledby={labelledBy}
      aria-describedby={describedBy}
      disabled={disabled}
      onClick={() => {
        onChange(!checked);
      }}
      className={cn(
        'relative inline-flex h-8 w-14 shrink-0 items-center rounded-full p-1 transition-colors duration-300 ease-out-soft',
        'disabled:cursor-not-allowed disabled:opacity-60',
        checked ? 'bg-accent' : 'bg-surface-sunk ring-1 ring-line',
      )}
    >
      <span
        aria-hidden
        className={cn(
          'size-6 rounded-full shadow-soft transition-transform duration-500 ease-spring',
          checked ? 'translate-x-6 bg-accent-ink' : 'translate-x-0 bg-surface',
        )}
      />
    </button>
  );
}
