import { HouseIcon, ShieldCheckIcon, SignOutIcon, type Icon } from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { Navigate, NavLink, Outlet, useNavigate } from 'react-router';
import { Logo } from '@/components/Logo';
import { MAIN_ID, SkipLink } from '@/components/SkipLink';
import { LanguageToggle, ThemeToggle } from '@/components/Toggles';
import { cn } from '@/lib/cn';
import { useLogout, useSaveLocale, useSession } from '@/lib/session';

interface Tab {
  to: string;
  labelKey: string;
  icon: Icon;
  end?: boolean;
}

const TABS: Tab[] = [
  { to: '/app', labelKey: 'app.nav.home', icon: HouseIcon, end: true },
  { to: '/app/privacy', labelKey: 'app.nav.privacy', icon: ShieldCheckIcon },
];

function DesktopTabs() {
  const { t } = useTranslation();
  return (
    <nav aria-label={t('app.nav.label')} className="hidden md:block">
      <ul className="flex items-center gap-1 rounded-full bg-surface-sunk p-1 ring-1 ring-line">
        {TABS.map((tab) => (
          <li key={tab.to}>
            <NavLink
              to={tab.to}
              end={tab.end ?? false}
              className={({ isActive }) =>
                cn(
                  'inline-flex min-h-10 items-center rounded-full px-4 text-sm font-semibold transition-colors duration-300 ease-out-soft',
                  isActive ? 'bg-surface text-ink shadow-soft' : 'text-ink-muted hover:text-ink',
                )
              }
            >
              {t(tab.labelKey)}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

function MobileTabs() {
  const { t } = useTranslation();
  return (
    <nav
      aria-label={t('app.nav.label')}
      className="fixed inset-x-3 bottom-3 z-30 rounded-full bg-surface/90 p-1.5 shadow-soft ring-1 ring-line backdrop-blur-xl md:hidden"
    >
      <ul className="grid grid-flow-col auto-cols-fr">
        {TABS.map(({ to, labelKey, icon: TabIcon, end }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={end ?? false}
              className={({ isActive }) =>
                cn(
                  'flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-full text-xs font-semibold transition-colors duration-300 ease-out-soft',
                  isActive ? 'bg-accent-soft text-accent' : 'text-ink-muted',
                )
              }
            >
              <TabIcon size={22} weight="light" aria-hidden />
              {t(labelKey)}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function AppLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();
  const saveLocale = useSaveLocale();

  if (session.isPending) {
    return (
      <p role="status" className="grid min-h-[100dvh] place-items-center text-ink-muted">
        {t('loading')}
      </p>
    );
  }
  if (!session.data) return <Navigate to="/" replace />;

  return (
    <div className="min-h-[100dvh] pb-28 md:pb-12">
      <SkipLink />
      <header className="sticky top-0 z-20 border-b border-line bg-canvas/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Logo to="/app" />
          <DesktopTabs />
          <div className="flex items-center gap-1.5">
            <LanguageToggle
              onChange={(locale) => {
                saveLocale.mutate(locale);
              }}
            />
            <span className="hidden sm:inline-flex">
              <ThemeToggle />
            </span>
            <button
              type="button"
              onClick={() => {
                logout.mutate(undefined, {
                  onSettled: () => {
                    void navigate('/', { replace: true });
                  },
                });
              }}
              aria-label={t('app.signOut')}
              className="inline-flex size-11 items-center justify-center rounded-full text-ink-soft ring-1 ring-line transition-colors duration-300 ease-out-soft hover:bg-surface-sunk hover:text-ink"
            >
              <SignOutIcon size={18} weight="light" aria-hidden />
            </button>
          </div>
        </div>
      </header>
      <main id={MAIN_ID} className="mx-auto max-w-5xl px-4 pt-10 sm:px-6">
        <Outlet />
      </main>
      <MobileTabs />
    </div>
  );
}
