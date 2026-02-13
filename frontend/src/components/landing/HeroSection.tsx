import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Logo } from '@/components/ui/Logo';
import { Button } from '@/components/ui/Button';
import { Sparkles, ShieldOff, Cpu, Pencil } from 'lucide-react';
import { getStats, type SiteStats } from '@/api/stats';
import type { Character } from '@/types';

const features = [
  { key: 'fantasy', icon: Sparkles, titleKey: 'hero.feature1.title', descKey: 'hero.feature1.desc' },
  { key: 'nocensor', icon: ShieldOff, titleKey: 'hero.feature2.title', descKey: 'hero.feature2.desc' },
  { key: 'providers', icon: Cpu, titleKey: 'hero.feature3.title', descKey: 'hero.feature3.desc' },
  { key: 'create', icon: Pencil, titleKey: 'hero.feature4.title', descKey: 'hero.feature4.desc' },
];

interface Props {
  popularCharacters: Character[];
  onBrowseClick: () => void;
}

export function HeroSection({ popularCharacters, onBrowseClick }: Props) {
  const { t } = useTranslation();
  const [stats, setStats] = useState<SiteStats | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  const avatarChars = popularCharacters.filter((c) => c.avatar_url).slice(0, 6);

  return (
    <>
      {/* Hero Banner */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-rose-950/30 via-neutral-900 to-neutral-900" />
        <div className="relative max-w-5xl mx-auto px-4 pt-12 pb-16 md:pt-20 md:pb-24 text-center">
          <Logo className="w-16 h-16 md:w-20 md:h-20 text-rose-500 mx-auto mb-6" />

          <h1 className="text-4xl md:text-6xl font-bold mb-4">
            <span className="text-white">Sweet</span>
            <span className="text-rose-500">Sin</span>
          </h1>

          <p className="text-xl md:text-2xl text-rose-300/80 font-medium mb-3">
            {t('hero.slogan')}
          </p>

          <p className="text-neutral-400 max-w-lg mx-auto mb-4 text-sm md:text-base">
            {t('hero.subtitle')}
          </p>

          {stats && (
            <div className="flex items-center justify-center gap-2 text-sm text-neutral-400 mb-6 flex-wrap">
              <span className="font-semibold text-white">{stats.users.toLocaleString()}+</span>
              <span>{t('stats.users')}</span>
              <span className="text-neutral-600 mx-1">&middot;</span>
              <span className="font-semibold text-white">{stats.messages.toLocaleString()}+</span>
              <span>{t('stats.messages')}</span>
              <span className="text-neutral-600 mx-1">&middot;</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="font-semibold text-green-400">{stats.online_now}</span>
              </span>
              <span>{t('stats.onlineNow')}</span>
            </div>
          )}

          <div className="flex items-center justify-center gap-3 mb-12">
            <Link to="/auth">
              <Button size="lg" className="px-8">{t('hero.cta')}</Button>
            </Link>
            <Button variant="secondary" size="lg" onClick={onBrowseClick}>
              {t('hero.browse')}
            </Button>
          </div>

          {avatarChars.length > 0 && (
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">
                {t('hero.popularTitle')}
              </p>
              <div className="flex items-center justify-center gap-3 flex-wrap">
                {avatarChars.map((char) => (
                  <Link to={`/character/${char.id}`} key={char.id} title={char.name}>
                    <img
                      src={char.avatar_url!}
                      alt={char.name}
                      className="w-12 h-12 md:w-14 md:h-14 rounded-full object-cover border-2 border-neutral-700 hover:border-rose-500 transition-colors"
                    />
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Feature Cards */}
      <section className="max-w-5xl mx-auto px-4 pb-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          {features.map((f) => (
            <div
              key={f.key}
              className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4 md:p-5 text-center"
            >
              <div className="w-10 h-10 rounded-lg bg-rose-600/10 flex items-center justify-center mx-auto mb-3">
                <f.icon className="w-5 h-5 text-rose-400" />
              </div>
              <h3 className="font-semibold text-white text-sm mb-1">{t(f.titleKey)}</h3>
              <p className="text-xs text-neutral-400 leading-relaxed">{t(f.descKey)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Divider */}
      <div className="max-w-5xl mx-auto px-4">
        <div className="border-t border-neutral-800" />
      </div>
    </>
  );
}
