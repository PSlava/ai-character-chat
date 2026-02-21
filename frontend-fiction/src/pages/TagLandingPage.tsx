import { useState, useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCharacters } from '@/api/characters';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { SEO } from '@/components/seo/SEO';
import { localePath } from '@/lib/lang';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Character } from '@/types';

// Same tag config used in backend (TAG_PAGES)
const TAG_CONFIG: Record<string, { searchValues: string[]; labelKey: string; descKey: string }> = {
  fantasy: { searchValues: ['фэнтези', 'fantasy', 'fantasía'], labelKey: 'tags.fantasy', descKey: 'tagPage.fantasyDesc' },
  romance: { searchValues: ['романтика', 'romance'], labelKey: 'tags.romance', descKey: 'tagPage.romanceDesc' },
  anime: { searchValues: ['аниме', 'anime'], labelKey: 'tags.anime', descKey: 'tagPage.animeDesc' },
  modern: { searchValues: ['современность', 'modern', 'moderno', 'реалистичный'], labelKey: 'tags.modern', descKey: 'tagPage.modernDesc' },
};

const PAGE_SIZE = 15;

export function TagLandingPage() {
  const { tagName } = useParams<{ tagName: string }>();
  const { t, i18n } = useTranslation();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const config = tagName ? TAG_CONFIG[tagName] : undefined;

  useEffect(() => {
    setPage(1);
  }, [tagName, i18n.language]);

  useEffect(() => {
    if (!config) return;
    setLoading(true);
    // Search for the first matching tag value
    getCharacters({
      tag: config.searchValues[0],
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      language: i18n.language,
    })
      .then((res) => {
        setCharacters(res.items);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  }, [tagName, page, i18n.language, config]);

  if (!config) return <Navigate to={localePath('/')} replace />;

  const label = t(config.labelKey);
  const description = t(config.descKey);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const url = localePath(`/tags/${tagName}`);

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <SEO
        title={`${label} — AI Characters`}
        description={description}
        url={url}
        jsonLd={{
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'CollectionPage',
              name: `${label} — AI Characters`,
              url: `${window.location.origin}${url}`,
              description,
              numberOfItems: total,
            },
            {
              '@type': 'BreadcrumbList',
              itemListElement: [
                { '@type': 'ListItem', position: 1, name: 'GrimQuill', item: window.location.origin },
                { '@type': 'ListItem', position: 2, name: t('home.title'), item: `${window.location.origin}${localePath('/')}` },
                { '@type': 'ListItem', position: 3, name: label },
              ],
            },
          ],
        }}
      />

      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">
          {label}
        </h1>
        <p className="text-neutral-400">{description}</p>
        {!loading && (
          <p className="text-neutral-500 text-sm mt-2">
            {t('tagPage.count', { count: total })}
          </p>
        )}
      </div>

      <CharacterGrid characters={characters} loading={loading} />

      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
            .reduce<(number | '...')[]>((acc, p, i, arr) => {
              if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push('...');
              acc.push(p);
              return acc;
            }, [])
            .map((p, i) =>
              p === '...' ? (
                <span key={`dots-${i}`} className="px-2 text-neutral-600">...</span>
              ) : (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`min-w-[36px] h-9 rounded-lg text-sm font-medium transition-colors ${
                    p === page
                      ? 'bg-purple-600 text-white'
                      : 'bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white'
                  }`}
                >
                  {p}
                </button>
              )
            )}
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
