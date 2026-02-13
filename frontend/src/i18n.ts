import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ru from './locales/ru.json';
import en from './locales/en.json';
import es from './locales/es.json';

const savedLang = localStorage.getItem('language');
const defaultLang = savedLang || 'en';

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, es: { translation: es }, ru: { translation: ru } },
  lng: defaultLang,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
