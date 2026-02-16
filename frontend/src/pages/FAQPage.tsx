import { useTranslation } from 'react-i18next';
import { SEO } from '@/components/seo/SEO';
import { localePath } from '@/lib/lang';

const FAQ_COUNT = 12;

export function FAQPage() {
  const { t } = useTranslation();

  const faqJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: Array.from({ length: FAQ_COUNT }, (_, i) => ({
      '@type': 'Question',
      name: t(`faq.q${i + 1}`),
      acceptedAnswer: {
        '@type': 'Answer',
        text: t(`faq.a${i + 1}`),
      },
    })),
  };

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <SEO title={t('faq.title')} description={t('seo.faq.description')} url={localePath('/faq')} jsonLd={faqJsonLd} />
      <h1 className="text-2xl font-bold mb-6">{t('faq.title')}</h1>
      <div className="space-y-6">
        {Array.from({ length: FAQ_COUNT }, (_, i) => i + 1).map((n) => (
          <div key={n} className="border-b border-neutral-800 pb-4 last:border-0">
            <h3 className="font-semibold text-white mb-2">{t(`faq.q${n}`)}</h3>
            <p className="text-neutral-400 text-sm leading-relaxed">{t(`faq.a${n}`)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
