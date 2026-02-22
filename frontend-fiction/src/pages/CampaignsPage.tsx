import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Swords, ScrollText, Dice5, Shield, Map, BookOpen, Users, Sparkles } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { getCampaigns, createCampaign, deleteCampaign } from '@/api/campaigns';
import { getCharacters } from '@/api/characters';
import { SEO } from '@/components/seo/SEO';
import type { Campaign, Character } from '@/types';
import toast from 'react-hot-toast';

const FEATURES = [
  { icon: Dice5, colorClass: 'text-amber-400 bg-amber-500/10', key: 'diceRolling' },
  { icon: Shield, colorClass: 'text-red-400 bg-red-500/10', key: 'combatTracker' },
  { icon: Map, colorClass: 'text-emerald-400 bg-emerald-500/10', key: 'exploration' },
  { icon: BookOpen, colorClass: 'text-blue-400 bg-blue-500/10', key: 'storytelling' },
  { icon: Users, colorClass: 'text-purple-400 bg-purple-500/10', key: 'npcs' },
  { icon: Sparkles, colorClass: 'text-yellow-400 bg-yellow-500/10', key: 'aiGm' },
];

const FEATURE_DEFAULTS: Record<string, { title: string; desc: string }> = {
  diceRolling: { title: 'Dice Rolling', desc: 'Full D&D dice system — d20, advantage, modifiers. Type [ROLL 2d6+3] anytime.' },
  combatTracker: { title: 'Combat Tracker', desc: 'Live HP bars, AC, conditions, and initiative. The GM tracks it all.' },
  exploration: { title: 'Open World', desc: 'Explore dungeons, cities, and wilderness. Your choices shape the story.' },
  storytelling: { title: 'Rich Narrative', desc: 'Detailed descriptions, memorable NPCs, and branching storylines.' },
  npcs: { title: 'Living NPCs', desc: 'Characters with motives, secrets, and relationships. Negotiate, fight, or befriend.' },
  aiGm: { title: 'AI Game Master', desc: 'A GM that adapts to your playstyle. Fair rules, creative improvisation.' },
};

export function CampaignsPage() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [adventures, setAdventures] = useState<Character[]>([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [loadingAdventures, setLoadingAdventures] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    getCharacters({ limit: 100, tag: 'dnd' })
      .then((res) => setAdventures('items' in res ? res.items : res as any))
      .catch(() => {})
      .finally(() => setLoadingAdventures(false));
  }, []);

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
    <>
      <SEO title={t('game.campaignsPageTitle', 'D&D Campaigns — AI Game Master')} />

      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-b from-amber-950/30 via-neutral-900 to-neutral-900 border-b border-amber-500/10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/5 via-transparent to-transparent" />
        <div className="relative max-w-4xl mx-auto px-4 py-12 sm:py-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium mb-4">
            <Swords className="w-3.5 h-3.5" />
            {t('game.heroLabel', 'D&D 5e Compatible')}
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
            <span className="text-white">{t('game.heroTitle1', 'Your AI')}</span>{' '}
            <span className="text-amber-400">{t('game.heroTitle2', 'Game Master')}</span>
          </h1>
          <p className="text-neutral-400 text-lg sm:text-xl max-w-2xl mx-auto mb-8">
            {t('game.heroSubtitle', 'Roll dice, explore dungeons, fight dragons, and make choices that matter. A Game Master that never cancels session night.')}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {isAuthenticated ? (
              <button
                onClick={() => setShowCreate(true)}
                className="flex items-center gap-2 px-6 py-3 bg-amber-600 hover:bg-amber-500 text-white rounded-xl font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                {t('game.newCampaign', 'New Campaign')}
              </button>
            ) : (
              <Link
                to="/auth?mode=register"
                className="flex items-center gap-2 px-6 py-3 bg-amber-600 hover:bg-amber-500 text-white rounded-xl font-medium transition-colors"
              >
                {t('game.startFree', 'Start Playing — Free')}
              </Link>
            )}
            <a
              href="#adventures"
              className="px-6 py-3 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-xl font-medium transition-colors"
            >
              {t('game.browseAdventures', 'Browse Adventures')}
            </a>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-4xl mx-auto px-4 py-10">
        <h2 className="text-xl font-bold text-center text-neutral-200 mb-8">
          {t('game.featuresTitle', 'Everything you need for a tabletop adventure')}
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, colorClass, key }) => {
            const def = FEATURE_DEFAULTS[key];
            return (
              <div key={key} className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
                <div className={`w-10 h-10 rounded-lg ${colorClass} flex items-center justify-center mb-3`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-neutral-200 text-sm mb-1">
                  {t(`game.feature.${key}.title`, def.title)}
                </h3>
                <p className="text-xs text-neutral-500 leading-relaxed">
                  {t(`game.feature.${key}.desc`, def.desc)}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Adventures */}
      <div id="adventures" className="max-w-4xl mx-auto px-4 pb-10">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-neutral-200">
            {t('game.availableAdventures', 'Available Adventures')}
          </h2>
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

        {loadingAdventures ? (
          <div className="grid grid-cols-1 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-36 bg-neutral-800 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {adventures.map((adv) => (
              <div
                key={adv.id}
                onClick={() => {
                  if (!isAuthenticated) { navigate('/auth?mode=register'); return; }
                  setShowCreate(true);
                }}
                className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-5 hover:border-amber-500/40 transition-colors cursor-pointer group"
              >
                <div className="flex items-start gap-4">
                  <div className="shrink-0">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg overflow-hidden border border-neutral-600 group-hover:border-amber-500/50 transition-colors">
                      {adv.avatar_url ? (
                        <img src={adv.avatar_url} alt={adv.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-neutral-700 flex items-center justify-center">
                          <Swords className="w-6 h-6 text-neutral-500" />
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-bold text-lg text-neutral-100 group-hover:text-amber-300 transition-colors">
                      {adv.name}
                    </h3>
                    {adv.tagline && (
                      <p className="text-sm text-neutral-400 mt-0.5">{adv.tagline}</p>
                    )}
                    {adv.personality && (
                      <p className="text-sm text-neutral-500 mt-2 line-clamp-2 leading-relaxed">
                        {adv.personality.slice(0, 200)}{adv.personality.length > 200 ? '...' : ''}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {adv.tags?.filter((tg: string) => tg !== 'dnd').slice(0, 5).map((tg: string) => (
                        <span key={tg} className="text-[11px] px-2 py-0.5 bg-amber-500/10 text-amber-400/80 border border-amber-500/20 rounded-full">
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
          <div className="mt-6 text-center">
            <Link
              to="/auth?mode=register"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-xl font-medium transition-colors"
            >
              {t('game.signUpToPlay', 'Sign up to start a campaign')}
            </Link>
          </div>
        )}
      </div>

      {/* User's Campaigns */}
      {isAuthenticated && (
        <div className="max-w-4xl mx-auto px-4 pb-10">
          <h2 className="text-xl font-bold text-neutral-200 mb-4">
            {t('game.yourCampaigns', 'Your Campaigns')}
          </h2>
          {loadingCampaigns ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-20 bg-neutral-800 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : campaigns.length === 0 ? (
            <div className="text-center py-8 text-neutral-500 bg-neutral-800/30 border border-neutral-700/50 rounded-xl">
              <ScrollText className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p>{t('game.noCampaigns', 'No campaigns yet. Create your first adventure!')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {campaigns.map((c) => (
                <Link
                  key={c.id}
                  to={`/campaigns/${c.id}`}
                  className="block bg-neutral-800/50 border border-neutral-700 rounded-xl p-4 hover:border-purple-500/50 transition-colors group"
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
        </div>
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
    </>
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
