import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGS } from '@/lib/lang';

const SITE_URL = 'https://sweetsin.cc';
const SITE_NAME = 'SweetSin';

interface SEOProps {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  jsonLd?: object;
}

/** Strip /:lang prefix to get base path */
function stripLangPrefix(path: string): string {
  const parts = path.split('/');
  if (parts.length >= 2 && SUPPORTED_LANGS.includes(parts[1])) {
    const rest = '/' + parts.slice(2).join('/');
    return rest === '/' ? '' : rest;
  }
  return path;
}

export function SEO({ title, description, image, url, jsonLd }: SEOProps) {
  const { i18n } = useTranslation();
  const fullTitle = title ? `${title} | ${SITE_NAME}` : `${SITE_NAME} — AI Character Chat`;
  const canonical = url ? `${SITE_URL}${url}` : `${SITE_URL}/${i18n.language}`;
  const ogImage = image?.startsWith('/') ? `${SITE_URL}${image}` : image;

  // Build per-language alternate URLs
  const basePath = url ? stripLangPrefix(url) : '';
  const langUrl = (lang: string) => `${SITE_URL}/${lang}${basePath}`;

  return (
    <Helmet>
      <html lang={i18n.language} />
      <title>{fullTitle}</title>
      {description && <meta name="description" content={description} />}
      <link rel="canonical" href={canonical} />
      <meta property="og:title" content={title || `${SITE_NAME} — AI Character Chat`} />
      {description && <meta property="og:description" content={description} />}
      {ogImage && <meta property="og:image" content={ogImage} />}
      <meta property="og:url" content={canonical} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content={SITE_NAME} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title || `${SITE_NAME} — AI Character Chat`} />
      {description && <meta name="twitter:description" content={description} />}
      {ogImage && <meta name="twitter:image" content={ogImage} />}
      <link rel="alternate" hrefLang="en" href={langUrl('en')} />
      <link rel="alternate" hrefLang="es" href={langUrl('es')} />
      <link rel="alternate" hrefLang="ru" href={langUrl('ru')} />
      <link rel="alternate" hrefLang="x-default" href={langUrl('en')} />
      {jsonLd && (
        <script type="application/ld+json">
          {JSON.stringify(jsonLd)}
        </script>
      )}
    </Helmet>
  );
}
