import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type SubmitEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { useCrisis } from '@/features/crisis/context';
import { apiFetch } from '@/lib/api';
import { cn } from '@/lib/cn';

interface Checkin {
  id: string;
  mood: number;
  energy: number;
  sleep_hours: number | null;
  note: string | null;
  created_at: string;
}

const KEY = ['checkins'] as const;

function Scale({
  name,
  label,
  value,
  onChange,
}: {
  name: string;
  label: string;
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-medium text-ink">{label}</legend>
      <div className="mt-2 grid grid-cols-5 gap-2">
        {[1, 2, 3, 4, 5].map((n) => (
          <label
            key={n}
            className={cn(
              'flex min-h-11 cursor-pointer items-center justify-center rounded-full font-semibold has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-accent',
              value === n ? 'bg-accent text-accent-ink' : 'bg-surface-sunk text-ink',
            )}
          >
            <input
              type="radio"
              name={name}
              value={n}
              checked={value === n}
              onChange={() => {
                onChange(n);
              }}
              className="sr-only"
            />
            {n}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function CheckinCard() {
  const { t, i18n } = useTranslation();
  const client = useQueryClient();
  const { openCrisis } = useCrisis();
  const [mood, setMood] = useState<number | null>(null);
  const [energy, setEnergy] = useState<number | null>(null);
  const [sleep, setSleep] = useState('');
  const [note, setNote] = useState('');

  const history = useQuery({
    queryKey: KEY,
    queryFn: ({ signal }) => apiFetch<Checkin[]>('/checkins', { signal }),
  });
  const save = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiFetch<Checkin & { safety_level: string }>('/checkins', { method: 'POST', body }),
    onSuccess: (saved) => {
      if (saved.safety_level === 'urgent') openCrisis();
      setMood(null);
      setEnergy(null);
      setSleep('');
      setNote('');
      void client.invalidateQueries({ queryKey: KEY });
    },
  });

  const onSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (mood === null || energy === null) return;
    save.mutate({
      mood,
      energy,
      sleep_hours: sleep === '' ? null : Number(sleep),
      note: note.trim() || null,
    });
  };

  const format = new Intl.DateTimeFormat(i18n.language === 'ta' ? 'ta-IN' : 'en-IN', {
    day: 'numeric',
    month: 'short',
  });

  return (
    <Bezel coreClassName="p-6 sm:p-8">
      <h2 className="font-display text-2xl font-semibold tracking-tight">{t('checkin.title')}</h2>
      <form onSubmit={onSubmit} className="mt-5 grid gap-5">
        <Scale name="mood" label={t('checkin.mood')} value={mood} onChange={setMood} />
        <Scale name="energy" label={t('checkin.energy')} value={energy} onChange={setEnergy} />
        <div className="grid gap-2">
          <label htmlFor="sleep" className="text-sm font-medium text-ink">
            {t('checkin.sleep')}
          </label>
          <input
            id="sleep"
            type="number"
            min={0}
            max={24}
            step={0.5}
            value={sleep}
            onChange={(e) => {
              setSleep(e.target.value);
            }}
            className="min-h-11 w-32 rounded-2xl bg-surface px-4 ring-1 ring-line focus:ring-2 focus:ring-accent focus:outline-none"
          />
        </div>
        <div className="grid gap-2">
          <label htmlFor="note" className="text-sm font-medium text-ink">
            {t('checkin.note')}
          </label>
          <textarea
            id="note"
            rows={2}
            maxLength={2000}
            value={note}
            onChange={(e) => {
              setNote(e.target.value);
            }}
            className="rounded-2xl bg-surface px-4 py-3 ring-1 ring-line focus:ring-2 focus:ring-accent focus:outline-none"
          />
          <p className="text-sm text-ink-muted">{t('checkin.noteHint')}</p>
        </div>
        <Button
          type="submit"
          disabled={mood === null || energy === null || save.isPending}
          className="justify-self-start"
        >
          {t('checkin.save')}
        </Button>
        <p aria-live="polite" className="min-h-5 text-sm font-medium text-accent">
          {save.isSuccess && t('checkin.saved')}
        </p>
      </form>
      {history.data && history.data.length > 0 && (
        <section aria-labelledby="recent-checkins" className="mt-4">
          <h3 id="recent-checkins" className="font-semibold">
            {t('checkin.recent')}
          </h3>
          <ul className="mt-2 grid gap-1 text-sm text-ink-soft">
            {history.data.slice(0, 7).map((c) => (
              <li key={c.id}>
                {t('checkin.row', {
                  date: format.format(new Date(c.created_at)),
                  mood: c.mood,
                  energy: c.energy,
                })}
              </li>
            ))}
          </ul>
        </section>
      )}
    </Bezel>
  );
}
