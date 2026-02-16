import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ru from './locales/ru.json';
import en from './locales/en.json';
import es from './locales/es.json';
import fr from './locales/fr.json';
import de from './locales/de.json';

// URL-first language detection: /:lang/... takes priority
const SUPPORTED = ['en', 'es', 'ru', 'fr', 'de'];
const pathLang = window.location.pathname.split('/')[1];
const urlLang = SUPPORTED.includes(pathLang) ? pathLang : null;
const savedLang = localStorage.getItem('language');
const browserLangs = navigator.languages || [navigator.language];
const browserLang = browserLangs.map((l) => l.split('-')[0]).find((l) => SUPPORTED.includes(l));
const defaultLang = urlLang || savedLang || browserLang || 'en';

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, es: { translation: es }, ru: { translation: ru }, fr: { translation: fr }, de: { translation: de } },
  lng: defaultLang,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
