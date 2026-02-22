import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Swords, ScrollText } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { getCampaigns, createCampaign, deleteCampaign } from '@/api/campaigns';
import { getCharacters } from '@/api/characters';
import { Avatar } from '@/components/ui/Avatar';
import type { Campaign, Character } from '@/types';
import toast from 'react-hot-toast';

export function CampaignsPage() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [adventures, setAdventures] = useState<Character[]>([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [loadingAdventures, setLoadingAdventures] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  // Load DnD adventures for everyone
  useEffect(() => {
    getCharacters({ limit: 100, tag: 'dnd' })
      .then((res) => setAdventures('items' in res ? res.items : res as any))
      .catch(() => {})
      .finally(() => setLoadingAdventures(false));
  }, []);

  // Load user campaigns only if authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      setLoadingCampaigns(false);
      return;
    }
    getCampaigns()
      .then(setCampaigns)
      .catch(() => {})
      .finally(() => setLoadingCampaigns(false));
  }, [isAuthenticated]);

  const handleDelete = async (id: string) => {
    if (!confirm(t('game.deleteCampaignConfirm', 'Delete this campaign?'))) return;
    try {
      await deleteCampaign(id);
      setCampaigns((prev) => prev.filter((c) => c.id !== id));
      toast.success(t('game.campaignDeleted', 'Campaign deleted'));
    } catch {
      toast.error(t('common.error', 'Error'));
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Swords className="w-6 h-6 text-purple-400" />
          {t('game.campaigns', 'Campaigns')}
        </h1>
        {isAuthenticated && (
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t('game.newCampaign', 'New Campaign')}
          </button>
        )}
      </div>

      {/* Available Adventures */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-neutral-300 mb-4">
          {t('game.availableAdventures', 'Available Adventures')}
        </h2>
        {loadingAdventures ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-neutral-800 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {adventures.map((adv) => (
              <div
                key={adv.id}
                onClick={() => {
                  if (!isAuthenticated) { navigate('/auth?mode=register'); return; }
                  setShowCreate(true);
                }}
                className="bg-neutral-800/50 border border-neutral-700 rounded-lg p-4 hover:border-purple-500/50 transition-colors cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  <Avatar src={adv.avatar_url} name={adv.name} size="md" />
                  <div className="min-w-0">
                    <h3 className="font-semibold text-neutral-200 group-hover:text-purple-300 transition-colors">
                      {adv.name}
                    </h3>
                    {adv.tagline && (
                      <p className="text-sm text-neutral-500 mt-0.5 line-clamp-2">{adv.tagline}</p>
                    )}
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {adv.tags?.filter((tg: string) => tg !== 'dnd').slice(0, 3).map((tg: string) => (
                        <span key={tg} className="text-[10px] px-1.5 py-0.5 bg-neutral-700 text-neutral-400 rounded">
                          {tg}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {!isAuthenticated && !loadingAdventures && adventures.length > 0 && (
          <p className="text-sm text-neutral-500 mt-3 text-center">
            <Link to="/auth?mode=register" className="text-purple-400 hover:text-purple-300">
              {t('game.signUpToPlay', 'Sign up to start a campaign')}
            </Link>
          </p>
        )}
      </section>

      {/* User's Campaigns */}
      {isAuthenticated && (
        <section>
          <h2 className="text-lg font-semibold text-neutral-300 mb-4">
            {t('game.yourCampaigns', 'Your Campaigns')}
          </h2>
          {loadingCampaigns ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-20 bg-neutral-800 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : campaigns.length === 0 ? (
            <div className="text-center py-8 text-neutral-500">
              <ScrollText className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p>{t('game.noCampaigns', 'No campaigns yet. Create your first adventure!')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {campaigns.map((c) => (
                <Link
                  key={c.id}
                  to={`/campaigns/${c.id}`}
                  className="block bg-neutral-800/50 border border-neutral-700 rounded-lg p-4 hover:border-purple-500/50 transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-neutral-200 group-hover:text-purple-300 transition-colors">
                        {c.name}
                      </h3>
                      {c.description && (
                        <p className="text-sm text-neutral-500 mt-1 line-clamp-2">{c.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-neutral-500">
                        <span className="uppercase">{c.system}</span>
                        <span>{c.session_count || 0} {t('game.sessions', 'sessions')}</span>
                        <span className={c.status === 'active' ? 'text-green-400' : 'text-neutral-600'}>
                          {c.status}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDelete(c.id); }}
                      className="p-2 text-neutral-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {showCreate && (
        <CreateCampaignModal
          onClose={() => setShowCreate(false)}
          onCreate={(c) => {
            setCampaigns((prev) => [c, ...prev]);
            setShowCreate(false);
          }}
        />
      )}
    </div>
  );
}

function CreateCampaignModal({ onClose, onCreate }: { onClose: () => void; onCreate: (c: Campaign) => void }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [characterId, setCharacterId] = useState('');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loadingChars, setLoadingChars] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    getCharacters({ limit: 100, tag: 'dnd' })
      .then((res) => setCharacters('items' in res ? res.items : res as any))
      .catch(() => {})
      .finally(() => setLoadingChars(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !characterId) return;
    setCreating(true);
    try {
      const result = await createCampaign({
        name: name.trim(),
        description: description.trim() || undefined,
        character_id: characterId,
      });
      onCreate({
        id: result.id,
        name: result.name,
        description: description.trim() || null,
        system: 'dnd5e',
        status: 'active',
        session_count: 1,
        created_at: new Date().toISOString(),
      });
      // Navigate to the first session's chat
      navigate(`/chat/${result.session.chat_id}`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-xl w-full max-w-md mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-bold mb-4">{t('game.newCampaign', 'New Campaign')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-neutral-400 mb-1">{t('game.campaignName', 'Campaign Name')}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('game.campaignNamePlaceholder', 'The Lost Mines of Phandelver')}
              className="w-full bg-neutral-800 border border-neutral-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-neutral-400 mb-1">{t('game.description', 'Description')}</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('game.descriptionPlaceholder', 'A brief description of your adventure...')}
              className="w-full bg-neutral-800 border border-neutral-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500 resize-none h-20"
            />
          </div>
          <div>
            <label className="block text-sm text-neutral-400 mb-1">{t('game.adventureTemplate', 'Adventure Template')}</label>
            {loadingChars ? (
              <div className="h-10 bg-neutral-800 rounded-lg animate-pulse" />
            ) : (
              <select
                value={characterId}
                onChange={(e) => setCharacterId(e.target.value)}
                className="w-full bg-neutral-800 border border-neutral-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                required
              >
                <option value="">{t('game.selectAdventure', 'Select an adventure...')}</option>
                {characters.map((ch) => (
                  <option key={ch.id} value={ch.id}>{ch.name}</option>
                ))}
              </select>
            )}
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-neutral-700 hover:bg-neutral-600 rounded-lg text-sm transition-colors"
            >
              {t('common.cancel', 'Cancel')}
            </button>
            <button
              type="submit"
              disabled={creating || !name.trim() || !characterId}
              className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
            >
              {creating ? '...' : t('game.startAdventure', 'Start Adventure')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
