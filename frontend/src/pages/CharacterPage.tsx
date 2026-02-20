import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCharacter, getCharacterBySlug, deleteCharacter, getSimilarCharacters, forkCharacter, getCharacterRelations, type CharacterRelation } from '@/api/characters';
import { createChat } from '@/api/chat';
import { getPersonas } from '@/api/personas';
import { useAuth } from '@/hooks/useAuth';
import { useChatStore } from '@/store/chatStore';
import { useFavoritesStore } from '@/store/favoritesStore';
import { useVotesStore } from '@/store/votesStore';
import { Avatar } from '@/components/ui/Avatar';
import { ImageLightbox } from '@/components/ui/ImageLightbox';
import { Button } from '@/components/ui/Button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { SEO } from '@/components/seo/SEO';
import { localePath } from '@/lib/lang';
import { isCharacterOnline } from '@/lib/utils';
import toast from 'react-hot-toast';
import { MessageCircle, Heart, User, Pencil, Trash2, Star, Flag, Download, ThumbsUp, ThumbsDown, GitFork } from 'lucide-react';
import { getExportUrl } from '@/api/export';
import { ReportModal } from '@/components/characters/ReportModal';
import { ShareButtons } from '@/components/characters/ShareButtons';
import { CharacterCard } from '@/components/characters/CharacterCard';
import type { Character, Persona } from '@/types';

export function CharacterPage() {
  const { id, slug } = useParams<{ id?: string; slug?: string }>();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { fetchChats } = useChatStore();
  const { favoriteIds, addFavorite: addFav, removeFavorite: removeFav } = useFavoritesStore();
  const { votes, vote } = useVotesStore();
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(false);
  const [forking, setForking] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showPersonaModal, setShowPersonaModal] = useState(false);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [forceNewChat, setForceNewChat] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [showAvatarLightbox, setShowAvatarLightbox] = useState(false);
  const [similar, setSimilar] = useState<Character[]>([]);
  const [relations, setRelations] = useState<CharacterRelation[]>([]);

  const isAdmin = user?.role === 'admin';
  const isOwner = isAuthenticated && character && (user?.id === character.creator_id || isAdmin);

  const tpl = (text: string) =>
    text.replace(/\{\{char\}\}/g, character?.name || '').replace(/\{\{user\}\}/g, user?.username || 'User');

  useEffect(() => {
    if (slug) {
      getCharacterBySlug(slug, i18n.language).then((c) => {
        setCharacter(c);
      });
    } else if (id) {
      getCharacter(id, i18n.language).then((c) => {
        setCharacter(c);
        // Redirect old UUID URL to slug URL
        if (c.slug) {
          navigate(localePath(`/c/${c.slug}`), { replace: true });
        }
      });
    }
  }, [id, slug, i18n.language]);

  useEffect(() => {
    if (character?.id) {
      getSimilarCharacters(character.id, i18n.language).then(setSimilar).catch(() => {});
      getCharacterRelations(character.id, i18n.language).then(setRelations).catch(() => {});
    }
  }, [character?.id, i18n.language]);

  const startChatWithPersona = async (personaId?: string, forceNew = false) => {
    if (!character) return;
    setShowPersonaModal(false);
    setLoading(true);
    try {
      const { chat } = await createChat(character.id, undefined, personaId, forceNew, i18n.language);
      setForceNewChat(false);
      await fetchChats();
      navigate(`/chat/${chat.id}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = async (forceNew = false) => {
    if (!character) return;

    // Anonymous user — create chat directly (no personas)
    if (!isAuthenticated) {
      setLoading(true);
      try {
        const { chat } = await createChat(character.id, undefined, undefined, false, i18n.language);
        navigate(`/chat/${chat.id}`);
      } catch (err: any) {
        if (err?.response?.status === 403) {
          // Anon chat disabled or limit reached — redirect to register
          navigate('/auth');
        } else {
          toast.error(t('toast.networkError'));
        }
      } finally {
        setLoading(false);
      }
      return;
    }

    // Authenticated user — fetch personas and decide flow
    try {
      const list = await getPersonas();
      setPersonas(list);
      if (list.length === 0) {
        // No personas — start directly
        startChatWithPersona(undefined, forceNew);
      } else if (list.length === 1 && list[0].is_default) {
        // Single default persona — use automatically
        startChatWithPersona(list[0].id, forceNew);
      } else {
        // Multiple personas — show picker
        setForceNewChat(forceNew);
        setShowPersonaModal(true);
      }
    } catch {
      // API error — start without persona
      startChatWithPersona(undefined, forceNew);
    }
  };

  const handleDelete = async () => {
    if (!character) return;
    setShowDeleteConfirm(false);
    setDeleting(true);
    try {
      await deleteCharacter(character.id);
      toast.success(t('toast.characterDeleted'));
      navigate('/');
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } }; message?: string };
      toast.error(ax?.response?.data?.detail || ax?.message || t('character.deleteError'));
      setDeleting(false);
    }
  };

  const handleFork = async () => {
    if (!character || !isAuthenticated) { navigate('/auth'); return; }
    setForking(true);
    try {
      const result = await forkCharacter(character.id);
      toast.success(t('toast.forked'));
      navigate(`/character/${result.id}/edit`);
    } catch {
      toast.error(t('toast.forkError'));
    } finally {
      setForking(false);
    }
  };

  const handleVote = async (value: number) => {
    if (!character || !isAuthenticated) { navigate('/auth'); return; }
    const currentVote = votes[character.id] || 0;
    const newValue = currentVote === value ? 0 : value;
    const result = await vote(character.id, newValue);
    if (result) {
      setCharacter((c) => c ? { ...c, vote_score: result.vote_score } : c);
    }
  };

  const userVote = character ? (votes[character.id] || 0) : 0;

  const charUrl = character?.slug ? localePath(`/c/${character.slug}`) : undefined;
  const charDescription = character
    ? (character.scenario || character.tagline || character.name).slice(0, 160)
    : undefined;

  if (!character) {
    return (
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6 mb-6">
          <div className="w-20 h-20 rounded-full bg-neutral-700/50 animate-pulse shrink-0" />
          <div className="flex-1 space-y-3 w-full">
            <div className="h-6 w-48 bg-neutral-700/50 rounded animate-pulse" />
            <div className="h-4 w-64 bg-neutral-700/50 rounded animate-pulse" />
            <div className="flex gap-4">
              <div className="h-4 w-16 bg-neutral-700/50 rounded animate-pulse" />
              <div className="h-4 w-16 bg-neutral-700/50 rounded animate-pulse" />
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="h-24 bg-neutral-800/50 rounded-xl animate-pulse" />
          <div className="h-32 bg-neutral-800/50 rounded-xl animate-pulse" />
          <div className="h-12 bg-neutral-700/50 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-full">
      <SEO
        title={character.tagline ? `${character.name} — ${character.tagline}` : character.name}
        description={charDescription}
        image={character.avatar_url || undefined}
        url={charUrl}
        jsonLd={{
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'CreativeWork',
              name: character.name,
              description: character.tagline || character.scenario || '',
              ...(character.avatar_url && { image: character.avatar_url.startsWith('/') ? `https://sweetsin.cc${character.avatar_url}` : character.avatar_url }),
              url: charUrl ? `https://sweetsin.cc${charUrl}` : undefined,
              keywords: character.tags.join(', '),
            },
            {
              '@type': 'BreadcrumbList',
              itemListElement: [
                { '@type': 'ListItem', position: 1, name: 'SweetSin', item: 'https://sweetsin.cc' },
                { '@type': 'ListItem', position: 2, name: t('home.title'), item: `https://sweetsin.cc${localePath('/')}` },
                { '@type': 'ListItem', position: 3, name: character.name },
              ],
            },
          ],
        }}
      />
      {character.avatar_url && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <img
            src={character.avatar_url}
            alt=""
            className="w-full h-full object-cover blur-3xl opacity-20 scale-110"
          />
        </div>
      )}
      <div className="relative p-4 md:p-6 max-w-3xl mx-auto">
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6 mb-6 md:mb-8">
        <div className="relative">
          <button
            type="button"
            onClick={() => character.avatar_url && setShowAvatarLightbox(true)}
            className={character.avatar_url ? 'cursor-pointer' : ''}
          >
            <Avatar src={character.avatar_url} name={character.name} size="lg" />
          </button>
          {isCharacterOnline(character.id) && (
            <span className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-neutral-800" />
          )}
        </div>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{character.name}</h1>
          {character.tagline && (
            <p className="text-neutral-400 mt-1">{character.tagline}</p>
          )}
          <div className="flex items-center gap-4 mt-3 text-sm text-neutral-500 min-w-0">
            <span className="flex items-center gap-1 shrink-0">
              <MessageCircle className="w-4 h-4" />
              {character.chat_count}
              {isAdmin && character.real_chat_count !== undefined && (
                <span className="text-emerald-500">({character.real_chat_count})</span>
              )}
              {' '}{t('character.chats')}
            </span>
            <button
              onClick={() => {
                if (!isAuthenticated) { navigate('/auth'); return; }
                if (favoriteIds.has(character.id)) {
                  removeFav(character.id);
                  setCharacter((c) => c ? { ...c, like_count: Math.max(0, c.like_count - 1) } : c);
                  toast.success(t('toast.unliked'));
                } else {
                  addFav(character.id);
                  setCharacter((c) => c ? { ...c, like_count: c.like_count + 1 } : c);
                  toast.success(t('toast.liked'));
                }
              }}
              className={`flex items-center gap-1 shrink-0 transition-colors ${
                favoriteIds.has(character.id)
                  ? 'text-rose-500 hover:text-rose-400'
                  : 'hover:text-rose-400'
              }`}
            >
              <Heart className={`w-4 h-4 ${favoriteIds.has(character.id) ? 'fill-current' : ''}`} />
              {character.like_count}
              {isAdmin && character.real_like_count !== undefined && (
                <span className="text-emerald-500">({character.real_like_count})</span>
              )}
            </button>
            <span className="flex items-center gap-1 shrink-0">
              <button onClick={() => handleVote(1)} className={`p-0.5 transition-colors ${userVote === 1 ? 'text-green-400' : 'hover:text-green-400'}`} title={t('character.upvote')}>
                <ThumbsUp className={`w-4 h-4 ${userVote === 1 ? 'fill-current' : ''}`} />
              </button>
              <span className={`min-w-[1ch] text-center ${(character.vote_score || 0) > 0 ? 'text-green-400' : (character.vote_score || 0) < 0 ? 'text-red-400' : ''}`}>
                {character.vote_score || 0}
              </span>
              <button onClick={() => handleVote(-1)} className={`p-0.5 transition-colors ${userVote === -1 ? 'text-red-400' : 'hover:text-red-400'}`} title={t('character.downvote')}>
                <ThumbsDown className={`w-4 h-4 ${userVote === -1 ? 'fill-current' : ''}`} />
              </button>
            </span>
            {(character.fork_count || 0) > 0 && (
              <span className="flex items-center gap-1 shrink-0">
                <GitFork className="w-4 h-4" />
                {character.fork_count} {t('character.forks')}
              </span>
            )}
            {character.profiles?.username && (
              <span className="flex items-center gap-1 min-w-0">
                <User className="w-4 h-4 shrink-0" />
                <span className="truncate">@{character.profiles.username}</span>
              </span>
            )}
          </div>
        </div>

        {isOwner && (
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/character/${character.id}/edit`)}
              className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
              title={t('common.edit')}
            >
              <Pencil className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={deleting}
              className="p-2 rounded-lg bg-neutral-800 hover:bg-red-900/50 text-neutral-400 hover:text-red-400 transition-colors"
              title={t('common.delete')}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
        {character.is_public && (
          <div className="flex gap-2">
            {isAuthenticated && !isOwner && (
              <button
                onClick={handleFork}
                disabled={forking}
                className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-purple-400 transition-colors"
                title={t('character.fork')}
              >
                <GitFork className="w-4 h-4" />
              </button>
            )}
            <a
              href={getExportUrl(character.id)}
              download={`${character.name}.json`}
              className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-blue-400 transition-colors"
              title="Export (SillyTavern)"
            >
              <Download className="w-4 h-4" />
            </a>
          </div>
        )}
        {isAuthenticated && !isOwner && (
          <button
            onClick={() => setShowReport(true)}
            className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-orange-400 transition-colors"
            title={t('report.title')}
          >
            <Flag className="w-4 h-4" />
          </button>
        )}
      </div>

      {character.forked_from_id && (
        <p className="text-xs text-neutral-500 mb-2">
          <GitFork className="w-3 h-3 inline mr-1" />
          {t('character.forkedFrom')}{' '}
          <button
            onClick={() => {
              getCharacter(character.forked_from_id!).then(c => {
                navigate(localePath(c.slug ? `/c/${c.slug}` : `/character/${c.id}`));
              }).catch(() => {});
            }}
            className="text-rose-400 hover:underline"
          >
            {character.name.replace(' (fork)', '')}
          </button>
        </p>
      )}

      {character.highlights && character.highlights.length > 0 && (
        <div className="mb-4">
          {character.highlights
            .filter(h => h.lang === i18n.language || (!character.highlights!.some(x => x.lang === i18n.language) && h.lang === 'en'))
            .slice(0, 2)
            .map((h, i) => (
              <p key={i} className="text-sm italic text-neutral-400">{h.text}</p>
            ))}
        </div>
      )}

      {character.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {character.tags.map((tag) => (
            <span
              key={tag}
              className="px-3 py-1 bg-neutral-800 rounded-full text-sm text-neutral-300"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {character.is_public && (
        <div className="mb-6">
          <ShareButtons
            name={character.name}
            tagline={character.tagline || undefined}
            url={`https://sweetsin.cc${charUrl || ''}`}
          />
        </div>
      )}

      {character.scenario && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-neutral-400 mb-2 uppercase tracking-wider">
            {t('character.scenario')}
          </h2>
          <p className="text-neutral-200 bg-neutral-800/50 rounded-xl p-4 whitespace-pre-wrap">
            {tpl(character.scenario)}
          </p>
        </div>
      )}

      {character.appearance && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-neutral-400 mb-2 uppercase tracking-wider">
            {t('character.appearance')}
          </h2>
          <p className="text-neutral-200 bg-neutral-800/50 rounded-xl p-4 whitespace-pre-wrap">
            {tpl(character.appearance)}
          </p>
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-sm font-medium text-neutral-400 mb-2 uppercase tracking-wider">
          {t('character.greeting')}
        </h2>
        <div className="bg-neutral-800/50 rounded-xl p-4 text-neutral-200 whitespace-pre-wrap">
          {tpl(character.greeting_message)}
        </div>
      </div>

      <Button onClick={() => handleStartChat()} disabled={loading} size="lg" className="w-full">
        {loading ? t('character.creatingChat') : t('character.startChat')}
      </Button>

      {relations.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-medium text-neutral-400 mb-3 uppercase tracking-wider">
            {t('character.connections')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {relations.map((rel) => (
              <div key={rel.character.id} className="relative">
                <span className="absolute top-2 right-2 z-10 px-2 py-0.5 bg-neutral-900/80 border border-neutral-600 rounded-full text-xs text-neutral-300">
                  {rel.label}
                </span>
                <CharacterCard character={rel.character} />
              </div>
            ))}
          </div>
        </div>
      )}

      {similar.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-medium text-neutral-400 mb-3 uppercase tracking-wider">
            {t('character.similar')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {similar.map((c) => (
              <CharacterCard key={c.id} character={c} />
            ))}
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <ConfirmDialog
          title={t('character.deleteTitle')}
          message={t('character.deleteConfirm')}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}

      {/* Persona selection modal */}
      {showPersonaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowPersonaModal(false)}>
          <div
            className="bg-neutral-900 border border-neutral-700 rounded-2xl p-5 sm:p-6 w-full max-w-sm mx-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-base font-semibold text-white mb-1">{t('persona.selectTitle')}</h3>
            <p className="text-sm text-neutral-400 mb-4">{t('persona.selectSubtitle')}</p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {/* No persona option */}
              <button
                onClick={() => startChatWithPersona(undefined, forceNewChat)}
                className="w-full text-left p-3 rounded-xl bg-neutral-800/50 border border-neutral-700 hover:border-neutral-500 transition-colors"
              >
                <span className="font-medium text-neutral-300">{t('persona.none')}</span>
                <span className="block text-xs text-neutral-500 mt-0.5">{t('persona.noneHint')}</span>
              </button>
              {/* Persona options */}
              {personas.map((p) => (
                <button
                  key={p.id}
                  onClick={() => startChatWithPersona(p.id, forceNewChat)}
                  className="w-full text-left p-3 rounded-xl bg-neutral-800/50 border border-neutral-700 hover:border-rose-500/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{p.name}</span>
                    {p.is_default && (
                      <Star className="w-3.5 h-3.5 text-amber-400" />
                    )}
                  </div>
                  {p.description && (
                    <p className="text-xs text-neutral-400 mt-1 line-clamp-2">{p.description}</p>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      {showReport && character && (
        <ReportModal characterId={character.id} onClose={() => setShowReport(false)} />
      )}
      {showAvatarLightbox && character?.avatar_url && (
        <ImageLightbox
          src={character.avatar_url}
          alt={character.name}
          onClose={() => setShowAvatarLightbox(false)}
        />
      )}
      </div>
    </div>
  );
}
