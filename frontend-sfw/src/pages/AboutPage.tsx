import { useTranslation } from 'react-i18next';
import { SEO } from '@/components/seo/SEO';
import { localePath } from '@/lib/lang';
import {
  Sparkles, Users, BookOpen, Brain, Layers, MessageCircle,
  Globe, Import, Sliders, Shield,
} from 'lucide-react';

const features = [
  { icon: Sparkles, key: 'personas' },
  { icon: Users, key: 'groupChats' },
  { icon: BookOpen, key: 'lorebooks' },
  { icon: Brain, key: 'memory' },
  { icon: Layers, key: 'multiChat' },
  { icon: Sliders, key: 'models' },
  { icon: Import, key: 'importExport' },
  { icon: Globe, key: 'multilingual' },
  { icon: MessageCircle, key: 'literary' },
  { icon: Shield, key: 'privacy' },
];

export function AboutPage() {
  const { t } = useTranslation();
  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      <SEO title={t('about.title')} description={t('seo.about.description')} url={localePath('/about')} />
      <h1 className="text-2xl font-bold mb-6">{t('about.title')}</h1>

      <div className="space-y-4 text-neutral-300 leading-relaxed mb-10">
        <p>{t('about.p1')}</p>
        <p>{t('about.p2')}</p>
        <p>{t('about.p3')}</p>
      </div>

      <h2 className="text-lg font-semibold text-white mb-5">{t('about.featuresTitle')}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        {features.map((f) => (
          <div key={f.key} className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4 flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-600/10 flex items-center justify-center shrink-0">
              <f.icon className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm mb-1">{t(`about.f.${f.key}.title`)}</h3>
              <p className="text-xs text-neutral-400 leading-relaxed">{t(`about.f.${f.key}.desc`)}</p>
            </div>
          </div>
        ))}
      </div>

      <h2 className="text-lg font-semibold text-white mb-3">{t('about.teamTitle')}</h2>
      <p className="text-neutral-300 leading-relaxed">{t('about.teamDesc')}</p>
    </div>
  );
}
