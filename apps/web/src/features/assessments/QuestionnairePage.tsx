import { ArrowLeftIcon, TranslateIcon } from '@phosphor-icons/react';
import { useEffect, useId, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useParams } from 'react-router';
import { Button } from '@/components/ui/Button';
import { useCrisis } from '@/features/crisis/context';
import { cn } from '@/lib/cn';
import type { Locale } from '@/lib/i18n';
import {
  INSTRUMENT_TYPES,
  PHQ9_SAFETY_ITEM,
  useInstrument,
  useSubmitAssessment,
  type AssessmentResult,
  type Instrument,
  type InstrumentType,
  type Option,
} from './api';
import { ResultView } from './ResultView';

function isInstrumentType(value: string | undefined): value is InstrumentType {
  return INSTRUMENT_TYPES.includes(value as InstrumentType);
}

interface ChoiceListProps {
  legend: string;
  legendLang?: string;
  options: Option[];
  value: number | null;
  onChange: (value: number) => void;
  headingRef: React.RefObject<HTMLHeadingElement | null>;
  lead?: string;
}

function ChoiceList({
  legend,
  legendLang,
  options,
  value,
  onChange,
  headingRef,
  lead,
}: ChoiceListProps) {
  const name = useId();
  return (
    <fieldset>
      <legend className="contents">
        {lead && (
          <span lang={legendLang} className="block text-ink-muted">
            {lead}
          </span>
        )}
        <h2
          ref={headingRef}
          tabIndex={-1}
          lang={legendLang}
          className="mt-3 block font-display text-[clamp(1.6rem,4.6vw,2.4rem)] leading-[1.15] font-semibold tracking-tight text-balance text-ink outline-none"
        >
          {legend}
        </h2>
      </legend>
      <div className="mt-8 grid gap-3">
        {options.map((option) => {
          const checked = value === option.value;
          return (
            <label
              key={option.value}
              lang={legendLang}
              className={cn(
                'flex min-h-16 cursor-pointer items-center gap-4 rounded-full px-6 text-lg transition-[background-color,color,box-shadow,transform] duration-300 ease-out-soft has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-accent active:scale-[0.99]',
                checked
                  ? 'bg-accent text-accent-ink shadow-soft'
                  : 'bg-surface text-ink ring-1 ring-line hover:bg-surface-sunk',
              )}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={checked}
                onChange={() => {
                  onChange(option.value);
                }}
                className="sr-only"
              />
              <span
                aria-hidden
                className={cn(
                  'flex size-5 shrink-0 items-center justify-center rounded-full',
                  checked ? 'bg-accent-ink' : 'ring-2 ring-ink-muted',
                )}
              >
                {checked && <span className="size-2 rounded-full bg-accent" />}
              </span>
              {option.label}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function Questionnaire({ instrument }: { instrument: Instrument }) {
  const { t } = useTranslation();
  const { openCrisis } = useCrisis();
  const submit = useSubmitAssessment(instrument.type);
  const heading = useRef<HTMLHeadingElement>(null);
  const crisisShown = useRef(false);

  const itemCount = instrument.items.length;
  const [answers, setAnswers] = useState<(number | null)[]>(() =>
    Array<number | null>(itemCount).fill(null),
  );
  const [step, setStep] = useState(0);
  const [difficulty, setDifficulty] = useState<number | null>(null);
  const [result, setResult] = useState<AssessmentResult | null>(null);

  useEffect(() => {
    heading.current?.focus();
  }, [step, result]);

  if (result) return <ResultView result={result} />;

  const onDifficultyStep = step === itemCount;
  const current = onDifficultyStep ? difficulty : (answers[step] ?? null);

  const choose = (value: number) => {
    if (onDifficultyStep) {
      setDifficulty(value);
      return;
    }
    setAnswers((prev) => prev.map((a, i) => (i === step ? value : a)));
    // Item 9 opens the safety flow the moment it is answered above zero, before any result.
    if (
      instrument.type === 'PHQ9' &&
      step === PHQ9_SAFETY_ITEM &&
      value > 0 &&
      !crisisShown.current
    ) {
      crisisShown.current = true;
      openCrisis();
    }
  };

  const finish = (functionalDifficulty: number | null) => {
    const complete = answers.filter((a): a is number => a !== null);
    if (complete.length !== itemCount) return;
    submit.mutate(
      { answers: complete, functional_difficulty: functionalDifficulty },
      {
        onSuccess: (saved) => {
          if (saved.safety_item_positive && !crisisShown.current) {
            crisisShown.current = true;
            openCrisis();
          }
          setResult(saved);
        },
      },
    );
  };

  const progress = Math.round((Math.min(step, itemCount) / itemCount) * 100);

  return (
    <div className="mx-auto max-w-2xl">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-semibold text-accent">{instrument.title}</p>
        <p className="text-sm text-ink-muted tabular-nums">
          {onDifficultyStep
            ? t('assessments.lastQuestion')
            : t('assessments.progress', { current: step + 1, total: itemCount })}
        </p>
      </div>
      <div
        role="progressbar"
        aria-label={t('assessments.progressLabel')}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
        className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-sunk"
      >
        <div
          className="h-full origin-left rounded-full bg-accent transition-transform duration-700 ease-out-soft"
          style={{ transform: `scaleX(${progress / 100})` }}
        />
      </div>

      {!instrument.translation_available && (
        <p className="mt-6 flex items-start gap-3 rounded-[1.25rem] bg-surface-sunk p-4 text-sm leading-relaxed text-ink-soft">
          <TranslateIcon
            size={20}
            weight="light"
            className="mt-0.5 shrink-0 text-accent"
            aria-hidden
          />
          {t('assessments.englishOnly')}
        </p>
      )}

      <div className="mt-10">
        {onDifficultyStep ? (
          <ChoiceList
            legend={instrument.difficulty_question}
            legendLang={instrument.item_locale}
            options={instrument.difficulty_options}
            value={current}
            onChange={choose}
            headingRef={heading}
          />
        ) : (
          <ChoiceList
            key={step}
            lead={instrument.stem}
            legend={instrument.items[step]?.text ?? ''}
            legendLang={instrument.item_locale}
            options={instrument.options}
            value={current}
            onChange={choose}
            headingRef={heading}
          />
        )}
      </div>

      <p aria-live="polite" className="mt-6 min-h-6 text-sm font-medium text-crisis">
        {submit.isError && t('errorGeneric')}
      </p>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <Button
          variant="quiet"
          disabled={step === 0 || submit.isPending}
          onClick={() => {
            setStep((s) => s - 1);
          }}
        >
          <ArrowLeftIcon size={16} weight="bold" aria-hidden />
          {t('assessments.back')}
        </Button>
        <div className="flex items-center gap-2">
          {onDifficultyStep && (
            <Button
              variant="secondary"
              disabled={submit.isPending}
              onClick={() => {
                finish(null);
              }}
            >
              {t('assessments.skip')}
            </Button>
          )}
          <Button
            arrow
            disabled={current === null || submit.isPending}
            onClick={() => {
              if (onDifficultyStep) finish(difficulty);
              else setStep((s) => s + 1);
            }}
          >
            {onDifficultyStep ? t('assessments.seeResult') : t('assessments.next')}
          </Button>
        </div>
      </div>

      <p className="mt-12 text-xs leading-relaxed text-ink-muted" lang="en">
        {instrument.attribution}
      </p>
    </div>
  );
}

export function QuestionnairePage() {
  const { t, i18n } = useTranslation();
  const { type } = useParams();
  const locale: Locale = i18n.language === 'ta' ? 'ta' : 'en';
  const instrumentType = isInstrumentType(type) ? type : 'PHQ9';
  const instrument = useInstrument(instrumentType, locale);

  if (!isInstrumentType(type)) return <Navigate to="/app/assessments" replace />;
  if (instrument.isPending) {
    return (
      <div
        className="mx-auto h-[28rem] max-w-2xl animate-pulse rounded-[1.75rem] bg-surface-sunk"
        aria-hidden
      />
    );
  }
  if (instrument.isError) return <p className="text-crisis">{t('errorGeneric')}</p>;

  return <Questionnaire key={`${type}-${locale}`} instrument={instrument.data} />;
}
