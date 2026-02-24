import { useEffect } from 'react';
import { useParams, Outlet, Navigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGS } from '@/lib/lang';

export function LangRoute() {
  const { lang } = useParams<{ lang: string }>();
  const { i18n } = useTranslation();
  const location = useLocation();

  // Sync i18n language with URL (hooks must be before any return)
  useEffect(() => {
    if (lang && SUPPORTED_LANGS.includes(lang) && i18n.language !== lang) {
      i18n.changeLanguage(lang);
      localStorage.setItem('language', lang);
    }
  }, [lang, i18n]);

  // Invalid language → redirect to /en/...
  if (!lang || !SUPPORTED_LANGS.includes(lang)) {
    const rest = location.pathname.replace(new RegExp(`^/${lang}`), '') || '/';
    const target = rest === '/' ? '/en' : `/en${rest}`;
    return <Navigate to={target + location.search + location.hash} replace />;
  }

  return <Outlet />;
}
