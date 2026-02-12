import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { getCharacters } from '@/api/characters';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import type { Character } from '@/types';

const PAGE_SIZE = 15;

export function HomePage() {
  const { t, i18n } = useTranslation();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const prevLangRef = useRef(i18n.language);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    // Reset to page 1 when search or language changes
    setPage(1);
  }, [search]);

  useEffect(() => {
    if (prevLangRef.current !== i18n.language) {
      prevLangRef.current = i18n.language;
      setPage(1);
    }
  }, [i18n.language]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      getCharacters({
        search: search || undefined,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
        language: i18n.language,
      })
        .then((res) => {
          setCharacters(res.items);
          setTotal(res.total);
        })
        .finally(() => setLoading(false));
    }, search ? 300 : 0);
    return () => clearTimeout(timer);
  }, [search, page, i18n.language]);

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">{t('home.title')}</h1>
        <p className="text-neutral-400">
          {t('home.subtitle')}
        </p>
      </div>

      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('home.search')}
          className="w-full bg-neutral-800 border border-neutral-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder-neutral-500 focus:outline-none focus:border-rose-500"
        />
      </div>

      <CharacterGrid characters={characters} loading={loading} />

      {/* Pagination */}
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
                      ? 'bg-rose-600 text-white'
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
