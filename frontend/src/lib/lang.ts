import i18n from '@/i18n';

export const SUPPORTED_LANGS = ['en', 'es', 'ru'];

const SEO_PATHS = ['/c/', '/about', '/terms', '/privacy', '/faq'];

function isSeoPath(path: string): boolean {
  if (path === '/') return true;
  return SEO_PATHS.some((p) => path === p || path.startsWith(p));
}

/**
 * Adds /{lang} prefix to SEO-relevant paths.
 * Non-SEO paths (/auth, /chat/*, /profile, /admin/*, etc.) returned as-is.
 */
export function localePath(path: string): string {
  const lang = i18n.language || 'en';

  if (!isSeoPath(path)) return path;

  // Avoid double-prefixing
  const first = path.split('/')[1];
  if (SUPPORTED_LANGS.includes(first)) return path;

  return path === '/' ? `/${lang}` : `/${lang}${path}`;
}
