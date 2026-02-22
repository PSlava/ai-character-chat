import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { getCharacters, suggestCharacters, type CharacterSuggestion } from '@/api/characters';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { HeroSection } from '@/components/landing/HeroSection';
import { SEO } from '@/components/seo/SEO';
import { localePath } from '@/lib/lang';
import { useAuth } from '@/hooks/useAuth';
import { getOnboardingPrefs } from '@/components/ui/OnboardingModal';
import { Search, ChevronLeft, ChevronRight, Swords, Dice5 } from 'lucide-react';
import type { Character } from '@/types';

const TAG_PILLS = [
  { key: 'all', labelKey: 'tags.all', value: null },
  { key: 'fantasy', labelKey: 'tags.fantasy', value: 'фэнтези' },
  { key: 'romance', labelKey: 'tags.romance', value: 'романтика' },
  { key: 'horror', labelKey: 'tags.horror', value: 'хоррор' },
  { key: 'sci_fi', labelKey: 'tags.sci_fi', value: 'sci-fi' },
  { key: 'mystery', labelKey: 'tags.mystery', value: 'детектив' },
  { key: 'adventure', labelKey: 'tags.adventure', value: 'приключения' },
  { key: 'modern', labelKey: 'tags.modern', value: 'современность' },
];

const PAGE_SIZE = 15;

export function HomePage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeTag, setActiveTag] = useState<string | null>(() => getOnboardingPrefs()?.tag ?? null);
  const [page, setPage] = useState(1);
  const prevLangRef = useRef(i18n.language);
  const gridRef = useRef<HTMLDivElement>(null);

  // Autocomplete state
  const [suggestions, setSuggestions] = useState<CharacterSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const suggestRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Apply onboarding preferences when onboarding completes
  useEffect(() => {
    const handler = () => {
      const prefs = getOnboardingPrefs();
      if (prefs) {
        setActiveTag(prefs.tag);
      }
    };
    window.addEventListener('onboarding-complete', handler);
    return () => window.removeEventListener('onboarding-complete', handler);
  }, []);

  useEffect(() => {
    // Reset to page 1 when search or tag changes
    setPage(1);
  }, [search, activeTag]);

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
        tag: activeTag || undefined,
        exclude_tag: 'dnd',
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
  }, [search, activeTag, page, i18n.language]);

  // Autocomplete suggestions
  useEffect(() => {
    if (!search || search.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const timer = setTimeout(() => {
      suggestCharacters(search, i18n.language)
        .then((res) => {
          setSuggestions(res);
          setShowSuggestions(res.length > 0);
          setSelectedIdx(-1);
        })
        .catch(() => setSuggestions([]));
    }, 200);
    return () => clearTimeout(timer);
  }, [search, i18n.language]);

  // Close suggestions on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (suggestRef.current && !suggestRef.current.contains(e.target as Node) &&
          inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearchKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && selectedIdx >= 0) {
      e.preventDefault();
      const s = suggestions[selectedIdx];
      navigate(localePath(s.slug ? `/c/${s.slug}` : `/character/${s.id}`));
      setShowSuggestions(false);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  }, [showSuggestions, suggestions, selectedIdx, navigate]);

  // Featured character of the day — pick from top 5 (already sorted by language preference)
  const featuredCharacter = characters.length > 0
    ? characters[Math.floor(Date.now() / 86400000) % Math.min(5, characters.length)]
    : null;

  const handleBrowseClick = () => {
    gridRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
      <SEO
        description={t('seo.home.description')}
        url={localePath('/')}
        jsonLd={{
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'WebSite',
              name: 'GrimQuill',
              url: window.location.origin,
              description: 'AI-Powered Interactive Fiction & D&D Game Master — Write Your Fate',
            },
            {
              '@type': 'Organization',
              name: 'GrimQuill',
              url: window.location.origin,
            },
          ],
        }}
      />
      {!authLoading && !isAuthenticated && (
        <HeroSection
          popularCharacters={characters}
          onBrowseClick={handleBrowseClick}
        />
      )}

      <div ref={gridRef} className="p-4 md:p-6 max-w-5xl mx-auto">
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">
            {isAuthenticated ? t('home.titleAuth') : t('home.title')}
          </h1>
          <p className="text-neutral-400">
            {t('home.subtitle')}
          </p>
        </div>

        {/* Genre filters */}
        <div className="flex flex-wrap gap-2 mb-4">
          {TAG_PILLS.map((tag) => (
            <button
              key={tag.key}
              onClick={() => setActiveTag(activeTag === tag.value ? null : tag.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                activeTag === tag.value || (tag.value === null && activeTag === null)
                  ? 'bg-purple-600 text-white'
                  : 'bg-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-700'
              }`}
            >
              {t(tag.labelKey)}
            </button>
          ))}
        </div>

        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500 z-10" />
          <input
            ref={inputRef}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            onKeyDown={handleSearchKeyDown}
            placeholder={t('home.search')}
            className="w-full bg-neutral-800 border border-neutral-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder-neutral-500 focus:outline-none focus:border-purple-500"
            autoComplete="off"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={suggestRef}
              className="absolute z-50 top-full mt-1 w-full bg-neutral-800 border border-neutral-700 rounded-xl shadow-xl overflow-hidden"
            >
              {suggestions.map((s, i) => (
                <Link
                  key={s.id}
                  to={localePath(s.slug ? `/c/${s.slug}` : `/character/${s.id}`)}
                  onClick={() => setShowSuggestions(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 transition-colors ${
                    i === selectedIdx ? 'bg-neutral-700' : 'hover:bg-neutral-700/50'
                  }`}
                >
                  {s.avatar_url ? (
                    <img src={s.avatar_url} alt="" className="w-8 h-8 rounded-full object-cover shrink-0" />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-neutral-600 shrink-0" />
                  )}
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">{s.name}</div>
                    {s.tagline && (
                      <div className="text-xs text-neutral-400 truncate">{s.tagline}</div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Featured character of the day */}
        {featuredCharacter && !search && !activeTag && !loading && (
          <Link
            to={localePath(featuredCharacter.slug ? `/c/${featuredCharacter.slug}` : `/character/${featuredCharacter.id}`)}
            className="block mb-6 p-4 rounded-xl bg-gradient-to-r from-purple-950/50 to-neutral-800/50 border border-purple-500/20 hover:border-purple-500/40 transition-colors"
          >
            <p className="text-xs text-purple-400 uppercase tracking-wider mb-3 font-medium">
              {t('featured.title')}
            </p>
            <div className="flex items-center gap-4">
              {featuredCharacter.avatar_url && (
                <div className="shrink-0">
                  <div className="w-16 h-16 rounded-full p-0.5 bg-gradient-to-br from-purple-500 to-indigo-600">
                    <img
                      src={featuredCharacter.avatar_url}
                      alt={featuredCharacter.name}
                      className="w-full h-full rounded-full object-cover"
                    />
                  </div>
                </div>
              )}
              <div className="min-w-0">
                <h3 className="font-semibold text-white text-lg">{featuredCharacter.name}</h3>
                {featuredCharacter.tagline && (
                  <p className="text-sm text-neutral-400 line-clamp-2">{featuredCharacter.tagline}</p>
                )}
              </div>
            </div>
          </Link>
        )}

        {/* D&D Adventures banner */}
        {!search && !activeTag && !loading && (
          <Link
            to="/campaigns"
            className="flex items-center gap-4 mb-6 p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-neutral-800/50 border border-amber-500/20 hover:border-amber-500/40 transition-colors group"
          >
            <div className="shrink-0 w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <Swords className="w-6 h-6 text-amber-400" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-amber-200 group-hover:text-amber-100 transition-colors">
                {t('home.dndBanner.title', 'D&D Game Master')}
              </h3>
              <p className="text-sm text-neutral-400">
                {t('home.dndBanner.subtitle', 'Roll dice, fight monsters, and forge your own adventure')}
              </p>
            </div>
            <Dice5 className="w-5 h-5 text-amber-500/50 group-hover:text-amber-400 transition-colors shrink-0" />
          </Link>
        )}

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
    </>
  );
}
