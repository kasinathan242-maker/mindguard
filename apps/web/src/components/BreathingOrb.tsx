import { PauseIcon, PlayIcon } from '@phosphor-icons/react';
import { motion, useReducedMotion } from 'motion/react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export type BreathPhase = 'in' | 'holdFull' | 'out' | 'holdEmpty';

const BOX_PHASES: BreathPhase[] = ['in', 'holdFull', 'out', 'holdEmpty'];
const PHASE_SECONDS = 4;

interface BreathingOrbProps {
  /** Starts paused when false. */
  autoPlay?: boolean;
  size?: 'md' | 'lg';
  /** Announce each phase to screen readers (use on the dedicated exercise screen only). */
  announce?: boolean;
}

/** Box breathing (4-4-4-4): the orb grows on the in-breath, rests, shrinks, rests. */
export function BreathingOrb({
  autoPlay = true,
  size = 'lg',
  announce = false,
}: BreathingOrbProps) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const [playing, setPlaying] = useState(autoPlay);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setIndex((i) => (i + 1) % BOX_PHASES.length);
    }, PHASE_SECONDS * 1000);
    return () => {
      window.clearInterval(timer);
    };
  }, [playing]);

  const phase = BOX_PHASES[index] ?? 'in';
  const expanded = phase === 'in' || phase === 'holdFull';
  const dimension = size === 'lg' ? 'size-56 sm:size-64' : 'size-40';

  return (
    <div className="flex flex-col items-center gap-5">
      <div className={`relative grid place-items-center ${dimension}`}>
        <motion.div
          aria-hidden
          className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_35%_30%,var(--accent-soft),transparent_70%)]"
          animate={
            reduce
              ? { scale: 1, opacity: 1 }
              : { scale: expanded ? 1.12 : 0.88, opacity: expanded ? 1 : 0.7 }
          }
          transition={{ duration: PHASE_SECONDS, ease: [0.37, 0, 0.63, 1] }}
        />
        <motion.div
          aria-hidden
          className="absolute inset-[14%] rounded-full bg-[radial-gradient(circle_at_40%_35%,color-mix(in_oklab,var(--accent)_55%,var(--surface)),var(--accent))] shadow-soft"
          initial={false}
          animate={reduce ? { scale: 1 } : { scale: expanded ? 1 : 0.62 }}
          transition={{ duration: PHASE_SECONDS, ease: [0.37, 0, 0.63, 1] }}
        />
      </div>
      <p
        aria-live={announce ? 'polite' : 'off'}
        className="min-h-8 font-display text-2xl font-medium text-ink"
      >
        {t(`breathing.${phase}`)}
      </p>
      <p className="sr-only">{t('breathing.description')}</p>
      <button
        type="button"
        onClick={() => {
          setPlaying((p) => !p);
        }}
        className="inline-flex min-h-11 items-center gap-2 rounded-full px-4 text-sm font-medium text-ink-soft ring-1 ring-line transition-colors duration-300 ease-out-soft hover:bg-surface-sunk"
      >
        {playing ? <PauseIcon size={16} weight="bold" /> : <PlayIcon size={16} weight="bold" />}
        {playing ? t('breathing.pause') : t('breathing.play')}
      </button>
    </div>
  );
}
