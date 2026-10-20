import { XIcon } from '@phosphor-icons/react';
import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { CrisisContext } from './context';
import { CrisisCard } from './CrisisCard';

/** Hosts one modal crisis dialog for the whole app, opened from anywhere via `useCrisis()`. */
export function CrisisProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const dialog = useRef<HTMLDialogElement>(null);
  // The card mounts only while open, so pages don't fetch resources nobody is looking at.
  const [open, setOpen] = useState(false);

  const openCrisis = useCallback(() => {
    const element = dialog.current;
    if (!element || element.open) return;
    setOpen(true);
    element.showModal();
  }, []);

  const value = useMemo(() => ({ openCrisis }), [openCrisis]);

  return (
    <CrisisContext value={value}>
      {children}
      <dialog
        ref={dialog}
        aria-labelledby="crisis-dialog-title"
        className="m-auto max-h-[calc(100dvh-1.5rem)] w-[calc(100%-1.5rem)] max-w-xl overflow-y-auto rounded-[1.75rem] bg-transparent p-0 backdrop:bg-ink/50 backdrop:backdrop-blur-sm"
        onClose={() => {
          setOpen(false);
        }}
        onClick={(event) => {
          if (event.target === event.currentTarget) event.currentTarget.close();
        }}
      >
        {open && (
          <div className="relative">
            <CrisisCard headingId="crisis-dialog-title" />
            <form method="dialog" className="absolute top-4 right-4">
              <button
                type="submit"
                aria-label={t('crisis.close')}
                className="inline-flex size-11 items-center justify-center rounded-full bg-surface/80 text-ink ring-1 ring-line"
              >
                <XIcon size={18} weight="bold" aria-hidden />
              </button>
            </form>
          </div>
        )}
      </dialog>
    </CrisisContext>
  );
}
