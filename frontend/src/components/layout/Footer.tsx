import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { localePath } from '@/lib/lang';
import { getCharacters } from '@/api/characters';
import type { Character } from '@/types';

// Module-level cache so we only fetch once across all mounts / navigations.
let cachedCharacters: Character[] | null = null;

export function Footer() {
  const { t, i18n } = useTranslation();
  const year = new Date().getFullYear();

  const [popularCharacters, setPopularCharacters] = useState<Character[]>(cachedCharacters ?? []);

  useEffect(() => {
    if (cachedCharacters) return;

    let cancelled = false;
    getCharacters({ limit: 8, language: i18n.language })
      .then((res) => {
        if (!cancelled) {
          cachedCharacters = res.items;
          setPopularCharacters(res.items);
        }
      })
      .catch(() => {
        // Silently ignore — footer links are supplemental.
      });

    return () => {
      cancelled = true;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <footer className="border-t border-neutral-800 mt-auto">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Popular Characters — SEO internal links */}
        {popularCharacters.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-neutral-400 mb-3 text-center">
              {t('footer.popularCharacters')}
            </h3>
            <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-sm">
              {popularCharacters.map((char) => (
                <Link
                  key={char.id}
                  to={localePath(char.slug ? `/c/${char.slug}` : `/character/${char.id}`)}
                  className="text-neutral-400 hover:text-rose-400 transition-colors"
                >
                  {char.name}
                </Link>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-6 text-sm text-neutral-500">
          <Link to={localePath('/about')} className="hover:text-neutral-300 transition-colors">
            {t('footer.about')}
          </Link>
          <Link to={localePath('/terms')} className="hover:text-neutral-300 transition-colors">
            {t('footer.terms')}
          </Link>
          <Link to={localePath('/privacy')} className="hover:text-neutral-300 transition-colors">
            {t('footer.privacy')}
          </Link>
          <Link to={localePath('/faq')} className="hover:text-neutral-300 transition-colors">
            {t('footer.faq')}
          </Link>
          <a href="mailto:support@sweetsin.cc" className="hover:text-neutral-300 transition-colors">
            {t('footer.contact')}
          </a>
        </div>
        <p className="text-center text-xs text-neutral-600 mt-3">
          {t('footer.copyright', { year })}
        </p>
      </div>
    </footer>
  );
}
