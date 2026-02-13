import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';

const SITE_URL = 'https://sweetsin.cc';
const SITE_NAME = 'SweetSin';

interface SEOProps {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  jsonLd?: object;
}

export function SEO({ title, description, image, url, jsonLd }: SEOProps) {
  const { i18n } = useTranslation();
  const fullTitle = title ? `${title} | ${SITE_NAME}` : `${SITE_NAME} — AI Character Chat`;
  const canonical = url ? `${SITE_URL}${url}` : SITE_URL;
  const ogImage = image?.startsWith('/') ? `${SITE_URL}${image}` : image;

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
      <link rel="alternate" hrefLang="en" href={canonical} />
      <link rel="alternate" hrefLang="es" href={canonical} />
      <link rel="alternate" hrefLang="ru" href={canonical} />
      <link rel="alternate" hrefLang="x-default" href={canonical} />
      {jsonLd && (
        <script type="application/ld+json">
          {JSON.stringify(jsonLd)}
        </script>
      )}
    </Helmet>
  );
}
