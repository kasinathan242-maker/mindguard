import { PauseIcon, PlayIcon } from '@phosphor-icons/react';
import { motion, useReducedMotion } from 'motion/react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { PATTERNS, type BreathPattern } from './breathing';

interface BreathingOrbProps {
  /** Starts paused when false. */
  autoPlay?: boolean;
  size?: 'md' | 'lg';
  pattern?: BreathPattern;
  /** Announce each phase to screen readers (use on the dedicated exercise screen only). */
  announce?: boolean;
  /** Short vibration at each phase change, where the device supports it. */
  haptics?: boolean;
}

/** The orb grows on the in-breath, rests, shrinks on the out-breath. */
export function BreathingOrb({
  autoPlay = true,
  size = 'lg',
  pattern = 'box',
  announce = false,
  haptics = false,
}: BreathingOrbProps) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const [playing, setPlaying] = useState(autoPlay);
  const [index, setIndex] = useState(0);
  const phases = PATTERNS[pattern];
  const [phase, seconds] = phases[index % phases.length] ?? ['in', 4];

  useEffect(() => {
    if (!playing) return;
    const timer = window.setTimeout(() => {
      setIndex((i) => (i + 1) % phases.length);
      if (haptics && typeof navigator.vibrate === 'function') navigator.vibrate(40);
    }, seconds * 1000);
    return () => {
      window.clearTimeout(timer);
    };
  }, [playing, index, seconds, phases.length, haptics]);

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
          transition={{ duration: seconds, ease: [0.37, 0, 0.63, 1] }}
        />
        <motion.div
          aria-hidden
          className="absolute inset-[14%] rounded-full bg-[radial-gradient(circle_at_40%_35%,color-mix(in_oklab,var(--accent)_55%,var(--surface)),var(--accent))] shadow-soft"
          initial={false}
          animate={reduce ? { scale: 1 } : { scale: expanded ? 1 : 0.62 }}
          transition={{ duration: seconds, ease: [0.37, 0, 0.63, 1] }}
        />
      </div>
      <p
        aria-live={announce ? 'polite' : 'off'}
        className="min-h-8 font-display text-2xl font-medium text-ink"
      >
        {t(`breathing.${phase}`)}
        <span className="ml-2 text-base text-ink-muted tabular-nums">{seconds}s</span>
      </p>
      <p className="sr-only">
        {t(pattern === 'box' ? 'breathing.description' : 'breathing.description478')}
      </p>
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
