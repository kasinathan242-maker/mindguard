import { motion, useReducedMotion } from 'motion/react';
import type { ReactNode } from 'react';
import { Logo } from '@/components/Logo';
import { MAIN_ID, SkipLink } from '@/components/SkipLink';
import { LanguageToggle } from '@/components/Toggles';
import { NeedHelpButton } from '@/features/crisis/NeedHelpButton';

export function OnboardingShell({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <div className="flex min-h-[100dvh] flex-col">
      <SkipLink />
      <header className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 pt-5 sm:px-6">
        <Logo />
        <div className="flex items-center gap-1.5">
          <NeedHelpButton compact />
          <LanguageToggle />
        </div>
      </header>
      <main
        id={MAIN_ID}
        className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-12 sm:px-6 sm:py-16"
      >
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
