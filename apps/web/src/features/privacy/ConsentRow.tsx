import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import { Switch } from '@/components/ui/Switch';
import type { ConsentScope } from '@/lib/session';

interface ConsentRowProps {
  scope: ConsentScope;
  checked: boolean;
  onChange: (checked: boolean) => void;
  required?: boolean;
  disabled?: boolean;
}

export function ConsentRow({ scope, checked, onChange, required, disabled }: ConsentRowProps) {
  const { t } = useTranslation();
  const id = useId();
  return (
    <div className="flex items-start justify-between gap-5 p-5 sm:p-6">
      <div>
        <p id={`${id}-label`} className="flex flex-wrap items-center gap-2 font-semibold text-ink">
          {t(`scopes.${scope}.label`)}
          {required && (
            <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-semibold text-accent">
              {t('privacyPage.required')}
            </span>
          )}
        </p>
        <p id={`${id}-body`} className="mt-1.5 max-w-[56ch] text-sm leading-relaxed text-ink-soft">
          {t(`scopes.${scope}.body`)}
        </p>
      </div>
      <Switch
        checked={checked}
        onChange={onChange}
        labelledBy={`${id}-label`}
        describedBy={`${id}-body`}
        {...(disabled === undefined ? {} : { disabled })}
      />
    </div>
  );
}
