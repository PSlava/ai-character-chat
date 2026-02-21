import { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Plus, MessageSquare, Swords } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { getCampaign, createSession } from '@/api/campaigns';
import type { CampaignDetail } from '@/types';
import toast from 'react-hot-toast';

export function CampaignDetailPage() {
  const { t } = useTranslation();
  const { campaignId } = useParams<{ campaignId: string }>();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth');
      return;
    }
    if (!campaignId) return;
    getCampaign(campaignId)
      .then(setCampaign)
      .catch(() => navigate('/campaigns'))
      .finally(() => setLoading(false));
  }, [isAuthenticated, campaignId, navigate]);

  const handleNewSession = async () => {
    if (!campaignId || creating) return;
    setCreating(true);
    try {
      const session = await createSession(campaignId);
      navigate(`/chat/${session.chat_id}`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to create session');
    } finally {
      setCreating(false);
    }
  };

  if (!isAuthenticated) return null;

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="h-8 w-48 bg-neutral-800 rounded animate-pulse mb-4" />
        <div className="h-4 w-72 bg-neutral-800 rounded animate-pulse mb-8" />
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-16 bg-neutral-800 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!campaign) return null;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link to="/campaigns" className="flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-300 mb-4 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        {t('game.backToCampaigns', 'Back to Campaigns')}
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Swords className="w-6 h-6 text-purple-400" />
            {campaign.name}
          </h1>
          {campaign.description && (
            <p className="text-neutral-400 mt-1">{campaign.description}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-neutral-500">
            <span className="uppercase">{campaign.system}</span>
            <span className={campaign.status === 'active' ? 'text-green-400' : 'text-neutral-600'}>
              {campaign.status}
            </span>
          </div>
        </div>
        <button
          onClick={handleNewSession}
          disabled={creating}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('game.newSession', 'New Session')}
        </button>
      </div>

      <h2 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-3">
        {t('game.sessions', 'Sessions')} ({campaign.sessions.length})
      </h2>

      {campaign.sessions.length === 0 ? (
        <p className="text-neutral-500 text-sm">{t('game.noSessions', 'No sessions yet.')}</p>
      ) : (
        <div className="space-y-2">
          {campaign.sessions.map((s) => (
            <Link
              key={s.id}
              to={`/chat/${s.chat_id}`}
              className="flex items-center gap-3 bg-neutral-800/50 border border-neutral-700 rounded-lg p-4 hover:border-purple-500/50 transition-colors group"
            >
              <MessageSquare className="w-5 h-5 text-neutral-600 group-hover:text-purple-400 transition-colors" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-neutral-300">
                    {t('game.session', 'Session')} #{s.number}
                  </span>
                  <span className={`text-xs ${s.status === 'active' ? 'text-green-400' : 'text-neutral-600'}`}>
                    {s.status}
                  </span>
                </div>
                {s.summary && (
                  <p className="text-sm text-neutral-500 mt-1 truncate">{s.summary}</p>
                )}
              </div>
              {s.created_at && (
                <span className="text-xs text-neutral-600 shrink-0">
                  {new Date(s.created_at).toLocaleDateString()}
                </span>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
