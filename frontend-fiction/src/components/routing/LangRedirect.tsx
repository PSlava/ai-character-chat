import { Navigate, useLocation } from 'react-router-dom';

/**
 * Redirects bare SEO paths (/, /c/:slug, /about, etc.) to /{lang}/...
 * Language detected from localStorage or defaults to 'en'.
 */
export function LangRedirect() {
  const location = useLocation();
  const lang = localStorage.getItem('language') || 'en';

  const path = location.pathname;
  const target = path === '/' ? `/${lang}` : `/${lang}${path}`;

  return <Navigate to={target + location.search + location.hash} replace />;
}
