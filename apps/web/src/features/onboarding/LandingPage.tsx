import {
  ChartLineUpIcon,
  ChatsCircleIcon,
  CheckIcon,
  FileArrowUpIcon,
  LockKeyIcon,
  PhoneIcon,
  ToggleLeftIcon,
  TrashIcon,
  UserCircleDashedIcon,
  XIcon,
  type Icon,
} from '@phosphor-icons/react';
import { motion, stagger, useReducedMotion, type Variants } from 'motion/react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router';
import { BreathingOrb } from '@/components/BreathingOrb';
import { Logo } from '@/components/Logo';
import { MAIN_ID, SkipLink } from '@/components/SkipLink';
import { LanguageToggle, ThemeToggle } from '@/components/Toggles';
import { Bezel } from '@/components/ui/Bezel';
import { ButtonLink } from '@/components/ui/Button';
import { NeedHelpButton } from '@/features/crisis/NeedHelpButton';
import { Reveal } from '@/components/ui/Reveal';
import { cn } from '@/lib/cn';

const TELE_MANAS_SHORT = '14416';
const TELE_MANAS_LONG = '1-800-891-4416';
const EMERGENCY = '112';

function SiteHeader() {
  const { t } = useTranslation();
  return (
    <header className="fixed inset-x-0 top-3 z-30 px-3 sm:top-5 sm:px-6">
      <nav
        aria-label={t('app.nav.label')}
        className="mx-auto flex max-w-5xl items-center justify-between gap-2 rounded-full bg-surface/80 py-1.5 pr-1.5 pl-3 shadow-soft ring-1 ring-line backdrop-blur-xl"
      >
        <Logo />
        <div className="hidden items-center gap-1 md:flex">
          <a
            href="#how"
            className="rounded-full px-4 py-2 text-sm font-medium text-ink-soft transition-colors duration-300 ease-out-soft hover:text-ink"
          >
            {t('nav.howItWorks')}
          </a>
          <a
            href="#privacy"
            className="rounded-full px-4 py-2 text-sm font-medium text-ink-soft transition-colors duration-300 ease-out-soft hover:text-ink"
          >
            {t('nav.privacy')}
          </a>
        </div>
        <div className="flex items-center gap-1">
          <NeedHelpButton compact className="px-3" />
          <LanguageToggle />
          <span className="hidden lg:inline-flex">
            <ThemeToggle />
          </span>
          <Link
            to="/login"
            className="inline-flex min-h-11 items-center rounded-full px-4 text-sm font-semibold text-ink transition-colors duration-300 ease-out-soft hover:bg-surface-sunk"
          >
            {t('nav.signIn')}
          </Link>
        </div>
      </nav>
    </header>
  );
}

const heroStagger: Variants = {
  hidden: {},
  show: { transition: { delayChildren: stagger(0.09, { startDelay: 0.05 }) } },
};

const heroItem: Variants = {
  hidden: { opacity: 0, y: 28, filter: 'blur(8px)' },
  show: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] },
  },
};

function Hero() {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const initial = reduce ? false : 'hidden';

  return (
    <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-28 pb-8 sm:px-6 md:min-h-[88dvh] md:grid-cols-[1.15fr_0.85fr] md:pt-24">
      <motion.div variants={heroStagger} initial={initial} animate="show" className="max-w-xl">
        <motion.h1
          variants={heroItem}
          className="font-display text-[clamp(2.4rem,6vw,4.25rem)] leading-[1.04] font-semibold tracking-tight text-balance text-ink"
        >
          {t('landing.hero.title')}
        </motion.h1>
        <motion.p
          variants={heroItem}
          className="mt-6 max-w-[46ch] text-lg leading-relaxed text-ink-soft"
        >
          {t('landing.hero.subtitle')}
        </motion.p>
        <motion.div variants={heroItem} className="mt-10 flex flex-wrap items-center gap-3">
          <ButtonLink to="/start" arrow>
            {t('landing.hero.cta')}
          </ButtonLink>
          <a
            href="#how"
            className="inline-flex min-h-12 items-center rounded-full px-5 font-medium text-ink-soft underline-offset-4 transition-colors duration-300 ease-out-soft hover:text-ink hover:underline"
          >
            {t('landing.hero.secondary')}
          </a>
        </motion.div>
      </motion.div>

      <motion.figure
        initial={reduce ? false : { opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
        className="w-full"
      >
        <Bezel coreClassName="flex flex-col items-center px-6 pt-10 pb-8 bg-[radial-gradient(120%_90%_at_50%_0%,var(--accent-soft),var(--surface)_70%)]">
          <BreathingOrb />
          <figcaption className="mt-6 text-center text-sm text-ink-muted">
            {t('breathing.caption')}
          </figcaption>
        </Bezel>
      </motion.figure>
    </section>
  );
}

function HonestSection() {
  const { t } = useTranslation();
  const is = t('landing.honest.is', { returnObjects: true }) as string[];
  const isNot = t('landing.honest.not', { returnObjects: true }) as string[];

  return (
    <section
      aria-labelledby="honest-title"
      className="mx-auto max-w-6xl px-4 py-24 sm:px-6 md:py-32"
    >
      <Reveal>
        <h2
          id="honest-title"
          className="max-w-2xl font-display text-[clamp(2rem,4.5vw,3.25rem)] leading-[1.08] font-semibold tracking-tight text-balance"
        >
          {t('landing.honest.title')}
        </h2>
      </Reveal>
      <div className="mt-14 grid gap-10 md:grid-cols-12 md:gap-8">
        <Reveal className="md:col-span-7">
          <h3 className="text-sm font-semibold text-accent">{t('landing.honest.isTitle')}</h3>
          <ul className="mt-6 space-y-5">
            {is.map((item) => (
              <li key={item} className="flex gap-4 text-lg leading-relaxed text-ink-soft">
                <span className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent">
                  <CheckIcon size={15} weight="bold" aria-hidden />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </Reveal>
        <Reveal delay={0.12} className="md:col-span-5 md:mt-10">
          <Bezel coreClassName="bg-surface-sunk p-7 sm:p-8">
            <h3 className="text-sm font-semibold text-ink">{t('landing.honest.notTitle')}</h3>
            <ul className="mt-6 space-y-5">
              {isNot.map((item) => (
                <li key={item} className="flex gap-4 leading-relaxed text-ink-soft">
                  <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full ring-1 ring-line">
                    <XIcon size={14} weight="bold" aria-hidden />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </Bezel>
        </Reveal>
      </div>
    </section>
  );
}

function SampleQuestion() {
  const { t } = useTranslation();
  const options = t('landing.how.sampleOptions', { returnObjects: true }) as string[];
  return (
    <div
      lang="en"
      className="mt-8 rounded-[1.25rem] bg-canvas p-5 ring-1 ring-line sm:p-6"
      aria-hidden
    >
      <p className="text-sm text-ink-muted">{t('landing.how.sampleLead')}</p>
      <p className="mt-2 font-display text-xl font-medium text-ink">
        {t('landing.how.sampleItem')}
      </p>
      <div className="mt-5 grid gap-2 sm:grid-cols-2">
        {options.map((option, index) => (
          <span
            key={option}
            className={cn(
              'flex min-h-11 items-center gap-3 rounded-full px-4 text-sm',
              index === 1
                ? 'bg-accent text-accent-ink'
                : 'bg-surface text-ink-soft ring-1 ring-line',
            )}
          >
            <span
              className={cn(
                'size-3 rounded-full',
                index === 1 ? 'bg-accent-ink' : 'ring-1 ring-ink-muted',
              )}
            />
            {option}
          </span>
        ))}
      </div>
    </div>
  );
}

function StepHeading({ icon: StepIcon, title, tone }: { icon: Icon; title: string; tone: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className={cn('flex size-10 items-center justify-center rounded-full', tone)}>
        <StepIcon size={20} weight="light" aria-hidden />
      </span>
      <h3 className="font-display text-2xl font-semibold tracking-tight">{title}</h3>
    </div>
  );
}

function HowItWorks() {
  const { t } = useTranslation();
  return (
    <section
      id="how"
      aria-labelledby="how-title"
      className="mx-auto max-w-6xl scroll-mt-28 px-4 py-24 sm:px-6 md:py-32"
    >
      <Reveal>
        <p className="inline-flex rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold tracking-[0.14em] text-accent uppercase">
          {t('landing.how.eyebrow')}
        </p>
        <h2
          id="how-title"
          className="mt-5 max-w-3xl font-display text-[clamp(2rem,4.5vw,3.25rem)] leading-[1.08] font-semibold tracking-tight text-balance"
        >
          {t('landing.how.title')}
        </h2>
      </Reveal>

      <ol className="mt-14 grid gap-4 md:grid-cols-6">
        <Reveal as="li" className="md:col-span-4 md:row-span-2">
          <Bezel coreClassName="p-7 sm:p-9">
            <StepHeading
              icon={ChartLineUpIcon}
              title={t('landing.how.answer.title')}
              tone="bg-accent-soft text-accent"
            />
            <p className="mt-4 max-w-[46ch] text-ink-soft">{t('landing.how.answer.body')}</p>
            <SampleQuestion />
          </Bezel>
        </Reveal>
        <Reveal as="li" delay={0.08} className="md:col-span-2">
          <Bezel coreClassName="bg-accent-soft p-7">
            <StepHeading
              icon={ChatsCircleIcon}
              title={t('landing.how.talk.title')}
              tone="bg-surface text-accent"
            />
            <p className="mt-4 text-ink-soft">{t('landing.how.talk.body')}</p>
          </Bezel>
        </Reveal>
        <Reveal as="li" delay={0.16} className="md:col-span-2">
          <Bezel coreClassName="bg-surface-sunk p-7">
            <StepHeading
              icon={FileArrowUpIcon}
              title={t('landing.how.connect.title')}
              tone="bg-surface text-ink"
            />
            <p className="mt-4 text-ink-soft">{t('landing.how.connect.body')}</p>
          </Bezel>
        </Reveal>
        <Reveal as="li" delay={0.08} className="md:col-span-6">
          <div className="flex flex-col gap-6 rounded-[1.75rem] bg-accent p-7 text-accent-ink sm:p-9 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <span className="flex size-10 items-center justify-center rounded-full bg-accent-ink/15">
                <CheckIcon size={20} weight="bold" aria-hidden />
              </span>
              <h3 className="font-display text-2xl font-semibold tracking-tight">
                {t('landing.how.review.title')}
              </h3>
            </div>
            <p className="max-w-[52ch] text-lg leading-relaxed opacity-90">
              {t('landing.how.review.body')}
            </p>
          </div>
        </Reveal>
      </ol>
    </section>
  );
}

const PROMISES: { key: 'anon' | 'encrypted' | 'off' | 'erase'; icon: Icon }[] = [
  { key: 'anon', icon: UserCircleDashedIcon },
  { key: 'encrypted', icon: LockKeyIcon },
  { key: 'off', icon: ToggleLeftIcon },
  { key: 'erase', icon: TrashIcon },
];

function PrivacyPromise() {
  const { t } = useTranslation();
  return (
    <section
      id="privacy"
      aria-labelledby="privacy-title"
      className="scroll-mt-28 border-y border-line bg-surface py-24 md:py-32"
    >
      <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 md:grid-cols-12">
        <Reveal className="md:col-span-5">
          <h2
            id="privacy-title"
            className="font-display text-[clamp(2.25rem,5vw,3.75rem)] leading-[1.04] font-semibold tracking-tight text-balance md:sticky md:top-32"
          >
            {t('landing.privacy.title')}
          </h2>
        </Reveal>
        <ul className="grid gap-x-8 gap-y-12 sm:grid-cols-2 md:col-span-7">
          {PROMISES.map(({ key, icon: PromiseIcon }, index) => (
            <Reveal as="li" key={key} delay={index * 0.07}>
              <PromiseIcon size={30} weight="light" className="text-accent" aria-hidden />
              <h3 className="mt-5 font-display text-xl font-semibold tracking-tight">
                {t(`landing.privacy.${key}.title`)}
              </h3>
              <p className="mt-2 leading-relaxed text-ink-soft">
                {t(`landing.privacy.${key}.body`)}
              </p>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  );
}

function HelpLine({ name, detail, number }: { name: string; detail: string; number: string }) {
  const { t } = useTranslation();
  return (
    <a
      href={`tel:${number.replace(/-/g, '')}`}
      className="group flex min-h-16 items-center justify-between gap-4 rounded-full bg-surface py-2 pr-2 pl-6 ring-1 ring-line transition-transform duration-500 ease-spring active:scale-[0.98]"
    >
      <span>
        <span className="block font-semibold text-ink">
          {name} <span className="font-display tabular-nums">{number}</span>
        </span>
        <span className="block text-sm text-ink-muted">{detail}</span>
      </span>
      <span
        className="flex size-12 shrink-0 items-center justify-center rounded-full bg-accent text-accent-ink transition-transform duration-500 ease-spring group-hover:scale-105"
        aria-hidden
      >
        <PhoneIcon size={20} weight="fill" />
      </span>
      <span className="sr-only">{t('landing.help.call', { number })}</span>
    </a>
  );
}

function HelpBand() {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="help-title" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
      <Reveal>
        <Bezel coreClassName="grid gap-8 bg-accent-soft p-7 sm:p-10 md:grid-cols-2 md:items-center">
          <div>
            <h2
              id="help-title"
              className="font-display text-3xl font-semibold tracking-tight text-balance"
            >
              {t('landing.help.title')}
            </h2>
            <p className="mt-3 max-w-[44ch] leading-relaxed text-ink-soft">
              {t('landing.help.body')}
            </p>
          </div>
          <div className="grid gap-3">
            <HelpLine
              name={t('landing.help.telemanas')}
              detail={`${t('landing.help.telemanasDetail')}. ${TELE_MANAS_LONG}`}
              number={TELE_MANAS_SHORT}
            />
            <HelpLine
              name={t('landing.help.emergency')}
              detail={t('landing.help.emergencyDetail')}
              number={EMERGENCY}
            />
          </div>
        </Bezel>
      </Reveal>
    </section>
  );
}

function FinalCta() {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="final-title" className="px-4 pt-8 pb-28 text-center sm:px-6">
      <Reveal className="mx-auto flex max-w-2xl flex-col items-center">
        <h2
          id="final-title"
          className="font-display text-[clamp(2.25rem,5vw,3.5rem)] leading-[1.05] font-semibold tracking-tight"
        >
          {t('landing.final.title')}
        </h2>
        <p className="mt-4 text-lg text-ink-soft">{t('landing.final.body')}</p>
        <ButtonLink to="/start" arrow className="mt-9">
          {t('landing.hero.cta')}
        </ButtonLink>
      </Reveal>
    </section>
  );
}

function SiteFooter() {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 text-sm text-ink-muted sm:px-6 md:flex-row md:items-center md:justify-between">
        <div className="max-w-xl space-y-2">
          <p>{t('landing.footer.disclaimer')}</p>
          <p>{t('landing.footer.made')}</p>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            to="/login"
            className="rounded-full px-4 py-2 font-medium text-ink-soft hover:text-ink"
          >
            {t('nav.signIn')}
          </Link>
        </div>
      </div>
    </footer>
  );
}

export function LandingPage() {
  return (
    <>
      <SkipLink />
      <SiteHeader />
      <main id={MAIN_ID}>
        <Hero />
        <HonestSection />
        <HowItWorks />
        <PrivacyPromise />
        <HelpBand />
        <FinalCta />
      </main>
      <SiteFooter />
    </>
  );
}
