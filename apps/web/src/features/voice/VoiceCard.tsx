import { MicrophoneIcon, StopIcon } from '@phosphor-icons/react';
import { useQuery } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { apiFetch } from '@/lib/api';
import { useConsents } from '@/lib/session';
import { toWav16k } from './wav';

interface Features {
  duration_s: number;
  pitch_median_hz: number | null;
  pause_ratio: number;
  onsets_per_second: number;
}

const MAX_MS = 30_000;

export function VoiceCard() {
  const { t } = useTranslation();
  const consents = useConsents();
  const status = useQuery({
    queryKey: ['voice-status'],
    queryFn: ({ signal }) => apiFetch<{ enabled: boolean }>('/voice/status', { signal }),
  });
  const [recording, setRecording] = useState(false);
  const [result, setResult] = useState<Features | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);

  const consented = consents.data?.items.find((c) => c.scope === 'voice')?.granted ?? false;
  if (!status.data?.enabled) return null;

  const start = async () => {
    setError(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: Blob[] = [];
      const media = new MediaRecorder(stream);
      media.ondataavailable = (e) => chunks.push(e.data);
      media.onstop = async () => {
        stream.getTracks().forEach((track) => {
          track.stop();
        });
        setRecording(false);
        const form = new FormData();
        form.append('file', await toWav16k(new Blob(chunks)), 'checkin.wav');
        const response = await fetch('/api/v1/voice/analyze', {
          method: 'POST',
          credentials: 'include',
          body: form,
        });
        if (response.ok) setResult((await response.json()) as Features);
        else setError(t('errorGeneric'));
      };
      recorder.current = media;
      media.start();
      setRecording(true);
      window.setTimeout(() => {
        if (media.state === 'recording') media.stop();
      }, MAX_MS);
    } catch {
      setError(t('voice.micBlocked'));
    }
  };

  return (
    <Bezel coreClassName="grid gap-3 p-6">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="font-display text-xl font-semibold">{t('voice.title')}</h2>
        <span className="rounded-full bg-surface-sunk px-3 py-1 text-xs font-semibold text-ink-soft">
          {t('voice.badge')}
        </span>
      </div>
      <p className="text-sm text-ink-soft">{t('voice.intro')}</p>
      {!consented ? (
        <p className="text-sm text-ink-muted">{t('voice.needsConsent')}</p>
      ) : recording ? (
        <Button
          variant="secondary"
          className="justify-self-start"
          onClick={() => {
            recorder.current?.stop();
          }}
        >
          <StopIcon size={16} weight="fill" aria-hidden />
          {t('voice.stop')}
        </Button>
      ) : (
        <Button variant="secondary" className="justify-self-start" onClick={() => void start()}>
          <MicrophoneIcon size={16} weight="bold" aria-hidden />
          {t('voice.record')}
        </Button>
      )}
      {result && (
        <p role="status" className="text-sm text-ink-soft">
          {t('voice.result', {
            seconds: result.duration_s,
            pitch: result.pitch_median_hz ?? '-',
            pauses: Math.round(result.pause_ratio * 100),
          })}
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm text-crisis">
          {error}
        </p>
      )}
    </Bezel>
  );
}
