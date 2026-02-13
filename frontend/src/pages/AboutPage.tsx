import { useTranslation } from 'react-i18next';

export function AboutPage() {
  const { t } = useTranslation();
  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">{t('about.title')}</h1>
      <div className="space-y-4 text-neutral-300 leading-relaxed">
        <p>{t('about.p1')}</p>
        <p>{t('about.p2')}</p>
        <p>{t('about.p3')}</p>
        <h2 className="text-lg font-semibold text-white pt-4">{t('about.teamTitle')}</h2>
        <p>{t('about.teamDesc')}</p>
      </div>
    </div>
  );
}
