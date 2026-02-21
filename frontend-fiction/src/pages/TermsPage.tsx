import { useTranslation } from 'react-i18next';
import { SEO } from '@/components/seo/SEO';
import { localePath } from '@/lib/lang';

export function TermsPage() {
  const { t } = useTranslation();
  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <SEO title={t('terms.title')} description={t('seo.terms.description')} url={localePath('/terms')} />
      <h1 className="text-2xl font-bold mb-4">{t('terms.title')}</h1>
      <p className="text-neutral-400 mb-6">{t('terms.intro')}</p>
      <div className="space-y-6 text-neutral-300 leading-relaxed">
        {[1, 2, 3, 4].map((n) => (
          <div key={n}>
            <h2 className="text-lg font-semibold text-white mb-2">
              {t(`terms.section${n}Title`)}
            </h2>
            <p>{t(`terms.section${n}`)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
