import { useTranslation } from 'react-i18next';
import { SEO } from '@/components/seo/SEO';

export function PrivacyPage() {
  const { t } = useTranslation();
  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <SEO title={t('privacy.title')} description={t('seo.privacy.description')} url="/privacy" />
      <h1 className="text-2xl font-bold mb-4">{t('privacy.title')}</h1>
      <p className="text-neutral-400 mb-6">{t('privacy.intro')}</p>
      <div className="space-y-6 text-neutral-300 leading-relaxed">
        {[1, 2, 3, 4].map((n) => (
          <div key={n}>
            <h2 className="text-lg font-semibold text-white mb-2">
              {t(`privacy.section${n}Title`)}
            </h2>
            <p>{t(`privacy.section${n}`)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
