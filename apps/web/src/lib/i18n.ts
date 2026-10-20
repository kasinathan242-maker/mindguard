import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enCommon from '@/locales/en/common.json';
import taCommon from '@/locales/ta/common.json';

export const SUPPORTED_LOCALES = ['en', 'ta'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

const STORAGE_KEY = 'mindguard.locale';

function initialLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'en' || stored === 'ta') return stored;
  } catch {
    // Storage unavailable (private mode); fall back to the browser language.
  }
  return navigator.language.toLowerCase().startsWith('ta') ? 'ta' : 'en';
}

export function setLocale(locale: Locale): void {
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // Not persisted; still applied for this visit.
  }
  void i18n.changeLanguage(locale);
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { common: enCommon },
    ta: { common: taCommon },
  },
  lng: initialLocale(),
  fallbackLng: 'en',
  defaultNS: 'common',
  interpolation: { escapeValue: false },
});

i18n.on('languageChanged', (lng) => {
  document.documentElement.lang = lng;
});
document.documentElement.lang = i18n.language;

export default i18n;
