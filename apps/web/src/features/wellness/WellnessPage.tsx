import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { BreathingOrb } from '@/components/BreathingOrb';
import type { BreathPattern } from '@/components/breathing';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { VoiceCard } from '@/features/voice/VoiceCard';
import { cn } from '@/lib/cn';
import { Reminders } from './Reminders';

function Timer() {
  const { t } = useTranslation();
  const [left, setLeft] = useState<number | null>(null);

  useEffect(() => {
    if (left === null || left <= 0) return;
    const id = window.setTimeout(() => {
      setLeft(left - 1);
    }, 1000);
    return () => {
      window.clearTimeout(id);
    };
  }, [left]);

  const mm = left === null ? '' : `${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`;
  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap gap-2">
        {[1, 3, 5].map((m) => (
          <Button
            key={m}
            variant="secondary"
            onClick={() => {
              setLeft(m * 60);
            }}
          >
            {t('wellness.minutes', { count: m })}
          </Button>
        ))}
      </div>
      {left !== null && (
        <p
          role="timer"
          aria-live="off"
          className="font-display text-4xl font-semibold tabular-nums"
        >
          {left === 0 ? t('wellness.timerDone') : mm}
        </p>
      )}
    </div>
  );
}

export function WellnessPage() {
  const { t } = useTranslation();
  const [pattern, setPattern] = useState<BreathPattern>('box');
  const grounding = t('crisis.groundingSteps', { returnObjects: true }) as string[];
  const prompts = t('wellness.prompts', { returnObjects: true }) as string[];

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="md:col-span-2">
        <h1 className="font-display text-[clamp(2rem,5vw,3rem)] leading-[1.08] font-semibold tracking-tight">
          {t('wellness.title')}
        </h1>
        <p className="mt-2 text-ink-soft">{t('wellness.intro')}</p>
      </div>
      <Bezel coreClassName="flex flex-col items-center gap-2 p-6 text-center">
        <h2 className="font-display text-xl font-semibold">{t('wellness.breathingTitle')}</h2>
        <div
          role="group"
          aria-label={t('wellness.pattern')}
          className="flex gap-1 rounded-full bg-surface-sunk p-1"
        >
          {(['box', '478'] as const).map((p) => (
            <button
              key={p}
              type="button"
              aria-pressed={pattern === p}
              onClick={() => {
                setPattern(p);
              }}
              className={cn(
                'min-h-9 rounded-full px-3 text-sm font-semibold',
                pattern === p ? 'bg-surface text-ink shadow-soft' : 'text-ink-muted',
              )}
            >
              {t(`wellness.patterns.${p}`)}
            </button>
          ))}
        </div>
        <BreathingOrb key={pattern} size="md" pattern={pattern} autoPlay={false} announce haptics />
      </Bezel>
      <Bezel coreClassName="p-6">
        <h2 className="font-display text-xl font-semibold">{t('wellness.groundingTitle')}</h2>
        <ol className="mt-3 grid gap-2">
          {grounding.map((step, i) => (
            <li key={step} className="flex gap-3 text-ink-soft">
              <span className="font-display font-semibold text-accent">{5 - i}</span>
              {step}
            </li>
          ))}
        </ol>
      </Bezel>
      <Bezel coreClassName="p-6">
        <h2 className="font-display text-xl font-semibold">{t('wellness.journalTitle')}</h2>
        <ul className="mt-3 grid gap-2 text-ink-soft">
          {prompts.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </Bezel>
      <div className="md:col-span-2">
        <VoiceCard />
      </div>
      <Bezel coreClassName="p-6">
        <h2 className="mb-3 font-display text-xl font-semibold">{t('wellness.timerTitle')}</h2>
        <Timer />
      </Bezel>
      <Bezel coreClassName="p-6 md:col-span-2">
        <h2 className="mb-3 font-display text-xl font-semibold">{t('reminders.title')}</h2>
        <Reminders />
      </Bezel>
    </div>
  );
}
