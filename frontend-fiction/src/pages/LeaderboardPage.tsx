import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getLeaderboard, type LeaderboardEntry, type LeaderboardSort } from '@/api/leaderboard';
import { Avatar } from '@/components/ui/Avatar';
import { SEO } from '@/components/seo/SEO';
import { Trophy, MessageCircle, BookOpen } from 'lucide-react';

const TABS: { key: LeaderboardSort; labelKey: string; icon: React.ReactNode }[] = [
  { key: 'level', labelKey: 'leaderboard.byLevel', icon: <Trophy className="w-4 h-4" /> },
  { key: 'messages', labelKey: 'leaderboard.byMessages', icon: <MessageCircle className="w-4 h-4" /> },
  { key: 'adventures', labelKey: 'leaderboard.byAdventures', icon: <BookOpen className="w-4 h-4" /> },
];

export function LeaderboardPage() {
  const { t } = useTranslation();
  const [sort, setSort] = useState<LeaderboardSort>('level');
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getLeaderboard(sort)
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [sort]);

  const getValue = (e: LeaderboardEntry) => {
    if (sort === 'messages') return e.message_count;
    if (sort === 'adventures') return e.chat_count;
    return `Lv.${e.level}`;
  };

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <SEO title={t('leaderboard.title')} />
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Trophy className="w-6 h-6 text-amber-400" />
          {t('leaderboard.title')}
        </h1>
        <p className="text-neutral-400 mt-1">{t('leaderboard.subtitle')}</p>
      </div>

      {/* Sort tabs */}
      <div className="flex gap-2 mb-6">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSort(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              sort === tab.key
                ? 'bg-purple-600 text-white'
                : 'bg-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-700'
            }`}
          >
            {tab.icon}
            {t(tab.labelKey)}
          </button>
        ))}
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-14 bg-neutral-800/50 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <p className="text-neutral-500 text-center py-12">{t('leaderboard.empty')}</p>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <div
              key={entry.rank}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-colors ${
                entry.rank <= 3
                  ? 'bg-amber-500/5 border-amber-500/20'
                  : 'bg-neutral-800/50 border-neutral-700'
              }`}
            >
              <span className={`w-8 text-center font-bold text-lg ${
                entry.rank === 1 ? 'text-amber-400' : entry.rank === 2 ? 'text-neutral-300' : entry.rank === 3 ? 'text-amber-600' : 'text-neutral-500'
              }`}>
                {entry.rank}
              </span>
              <Avatar
                src={entry.avatar_url}
                name={entry.display_name || entry.username}
                size="sm"
              />
              <span className="flex-1 min-w-0 truncate font-medium text-white">
                {entry.display_name || entry.username}
              </span>
              <span className="text-sm font-semibold text-purple-400 shrink-0">
                {getValue(entry)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
