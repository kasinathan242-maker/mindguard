import { useTranslation } from 'react-i18next';
import { BreathingOrb } from '@/components/BreathingOrb';
import { Bezel } from '@/components/ui/Bezel';
import { ButtonLink } from '@/components/ui/Button';
import { Reveal } from '@/components/ui/Reveal';
import { CheckinCard } from '@/features/checkin/CheckinCard';
import { useSession } from '@/lib/session';

export function HomePage() {
  const { t } = useTranslation();
  const { data: user } = useSession();

  return (
    <div className="grid gap-6 md:grid-cols-12">
      <Reveal className="md:col-span-12">
        <h1 className="font-display text-[clamp(2rem,5vw,3rem)] leading-[1.08] font-semibold tracking-tight">
          {t('app.home.greeting')}
        </h1>
      </Reveal>

      <Reveal className="md:col-span-12" delay={0.03}>
        <CheckinCard />
      </Reveal>

      {user?.is_anonymous && (
        <Reveal className="md:col-span-7" delay={0.05}>
          <Bezel coreClassName="flex h-full flex-col justify-between gap-6 p-6 sm:p-8">
            <div>
              <h2 className="font-display text-2xl font-semibold tracking-tight">
                {t('app.home.anonTitle')}
              </h2>
              <p className="mt-3 max-w-[52ch] leading-relaxed text-ink-soft">
                {t('app.home.anonBody')}
              </p>
            </div>
            <ButtonLink to="/app/privacy#account" variant="secondary" className="self-start">
              {t('app.home.anonCta')}
            </ButtonLink>
          </Bezel>
        </Reveal>
      )}

      <Reveal className={user?.is_anonymous ? 'md:col-span-5' : 'md:col-span-6'} delay={0.1}>
        <Bezel coreClassName="flex h-full flex-col items-center gap-2 bg-[radial-gradient(120%_90%_at_50%_0%,var(--accent-soft),var(--surface)_70%)] p-6 text-center sm:p-8">
          <h2 className="font-display text-xl font-semibold tracking-tight">
            {t('app.home.breatheTitle')}
          </h2>
          <p className="mb-4 text-sm text-ink-muted">{t('app.home.breatheBody')}</p>
          <BreathingOrb size="md" autoPlay={false} />
        </Bezel>
      </Reveal>
    </div>
  );
}
