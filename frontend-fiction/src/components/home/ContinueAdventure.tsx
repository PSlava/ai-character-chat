import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getRecentCampaigns, type RecentCampaign } from '@/api/campaigns';
import { Avatar } from '@/components/ui/Avatar';
import { PlayCircle } from 'lucide-react';

export function ContinueAdventure() {
  const { t } = useTranslation();
  const [campaigns, setCampaigns] = useState<RecentCampaign[]>([]);

  useEffect(() => {
    getRecentCampaigns(3).then(setCampaigns).catch(() => {});
  }, []);

  if (campaigns.length === 0) return null;

  return (
    <div className="mb-6">
      <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">
        {t('home.continueAdventure')}
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {campaigns.map((c) => (
          <Link
            key={c.id}
            to={`/chat/${c.chat_id}`}
            className="flex items-center gap-3 p-3 rounded-xl bg-neutral-800/50 border border-neutral-700 hover:border-purple-500/40 transition-colors group"
          >
            <Avatar
              src={c.character_avatar_url}
              name={c.character_name || c.name}
              size="md"
            />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-white truncate group-hover:text-purple-300 transition-colors">
                {c.character_name || c.name}
              </p>
              <p className="text-xs text-neutral-500">
                {t('home.continueSession', { number: c.session_number })}
              </p>
              <p className="text-[10px] text-neutral-600">
                {t('home.lastPlayed', { date: new Date(c.last_played).toLocaleDateString() })}
              </p>
            </div>
            <PlayCircle className="w-5 h-5 text-purple-500/50 group-hover:text-purple-400 shrink-0 transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}
