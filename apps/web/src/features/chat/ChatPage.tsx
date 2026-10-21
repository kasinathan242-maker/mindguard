import { PaperPlaneRightIcon } from '@phosphor-icons/react';
import { useMutation } from '@tanstack/react-query';
import { useEffect, useRef, useState, type SubmitEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Bezel } from '@/components/ui/Bezel';
import { Button } from '@/components/ui/Button';
import { CrisisCard } from '@/features/crisis/CrisisCard';
import { apiFetch } from '@/lib/api';
import { cn } from '@/lib/cn';
import { sendMessage } from './stream';

interface Message {
  id: number;
  role: 'user' | 'assistant' | 'crisis';
  content: string;
}

interface SessionInfo {
  id: string;
  stores_history: boolean;
}

export function ChatPage() {
  const { t } = useTranslation();
  const [chat, setChat] = useState<SessionInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [emotion, setEmotion] = useState<string | null>(null);
  const [emotionAnswered, setEmotionAnswered] = useState(false);
  const nextId = useRef(0);
  const end = useRef<HTMLDivElement>(null);

  const start = useMutation({
    mutationFn: () => apiFetch<SessionInfo>('/chat/sessions', { method: 'POST' }),
    onSuccess: setChat,
  });
  const { mutate: startChat } = start;
  useEffect(() => {
    startChat();
  }, [startChat]);
  useEffect(() => {
    end.current?.scrollIntoView({ block: 'end' });
  }, [messages]);

  const onSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !chat || busy) return;
    const history = messages
      .filter((m): m is Message & { role: 'user' | 'assistant' } => m.role !== 'crisis')
      .map(({ role, content: text }) => ({ role, content: text }));
    const userMessage: Message = { id: nextId.current++, role: 'user', content };
    const reply: Message = { id: nextId.current++, role: 'assistant', content: '' };
    setMessages((prev) => [...prev, userMessage]);
    setDraft('');
    setBusy(true);
    setFailed(false);
    try {
      for await (const evt of sendMessage(chat.id, content, chat.stores_history ? [] : history)) {
        if (evt.type === 'safety') {
          if (evt.level !== 'none') setPinned(true);
        } else if (evt.type === 'emotion') {
          const known = !['uncertain', 'unsupported', 'neutral'].includes(evt.label);
          setEmotion(known ? evt.label : null);
          setEmotionAnswered(false);
        } else if (evt.type === 'crisis') {
          setMessages((prev) => [...prev, { id: nextId.current++, role: 'crisis', content: '' }]);
        } else if (evt.type === 'token') {
          reply.content += evt.text;
          setMessages((prev) => [...prev.filter((m) => m.id !== reply.id), { ...reply }]);
        }
      }
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="font-display text-[clamp(2rem,5vw,3rem)] leading-[1.08] font-semibold tracking-tight">
          {t('chat.title')}
        </h1>
        <p className="mt-2 text-ink-soft">{t('chat.intro')}</p>
        {chat && (
          <p className="mt-1 text-sm text-ink-muted">
            {chat.stores_history ? t('chat.historyOn') : t('chat.historyOff')}
          </p>
        )}
      </div>

      {pinned && (
        <section
          aria-label={t('chat.pinnedLabel')}
          className="rounded-[1.25rem] bg-surface-sunk p-4 text-sm text-ink"
        >
          {t('chat.pinned')}
        </section>
      )}

      <Bezel coreClassName="flex min-h-[50dvh] flex-col gap-3 p-4 sm:p-6">
        <div
          role="log"
          aria-live="polite"
          aria-label={t('chat.logLabel')}
          className="flex flex-col gap-3"
        >
          {messages.length === 0 && <p className="text-ink-muted">{t('chat.empty')}</p>}
          {messages.map((m) =>
            m.role === 'crisis' ? (
              <CrisisCard key={m.id} headingId={`crisis-${m.id}`} />
            ) : (
              <p
                key={m.id}
                className={cn(
                  'max-w-[85%] rounded-[1.25rem] px-4 py-3 leading-relaxed',
                  m.role === 'user'
                    ? 'self-end bg-accent text-accent-ink'
                    : 'self-start bg-surface-sunk text-ink',
                )}
              >
                {m.content || '…'}
              </p>
            ),
          )}
          <div ref={end} />
        </div>
      </Bezel>

      {emotion && !emotionAnswered && (
        <div
          role="status"
          className="flex flex-wrap items-center gap-2 self-start rounded-full bg-surface-sunk px-4 py-2 text-sm text-ink-soft"
        >
          <span>{t('chat.emotionGuess', { emotion: t(`chat.emotions.${emotion}`) })}</span>
          <span className="text-ink-muted">{t('chat.emotionAsk')}</span>
          <button
            type="button"
            className="min-h-9 rounded-full px-3 font-semibold text-accent"
            onClick={() => {
              setEmotionAnswered(true);
            }}
          >
            {t('chat.yes')}
          </button>
          <button
            type="button"
            className="min-h-9 rounded-full px-3 font-semibold text-ink-soft"
            onClick={() => {
              setEmotionAnswered(true);
            }}
          >
            {t('chat.notReally')}
          </button>
        </div>
      )}

      {failed && (
        <p role="alert" className="text-sm font-medium text-crisis">
          {t('errorGeneric')}
        </p>
      )}

      <form onSubmit={(e) => void onSubmit(e)} className="flex items-end gap-2">
        <label htmlFor="chat-input" className="sr-only">
          {t('chat.inputLabel')}
        </label>
        <textarea
          id="chat-input"
          rows={2}
          maxLength={4000}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
          }}
          placeholder={t('chat.placeholder')}
          className="min-h-14 flex-1 resize-none rounded-2xl bg-surface px-4 py-3 text-ink ring-1 ring-line placeholder:text-ink-muted focus:ring-2 focus:ring-accent focus:outline-none"
        />
        <Button type="submit" disabled={busy || !chat || !draft.trim()} aria-label={t('chat.send')}>
          <PaperPlaneRightIcon size={18} weight="bold" aria-hidden />
        </Button>
      </form>
      <p className="text-xs text-ink-muted">{t('chat.disclaimer')}</p>
    </div>
  );
}
