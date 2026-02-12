import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCharacter, deleteCharacter } from '@/api/characters';
import { createChat } from '@/api/chat';
import { getPersonas } from '@/api/personas';
import { useAuth } from '@/hooks/useAuth';
import { useChatStore } from '@/store/chatStore';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { MessageCircle, Heart, User, Pencil, Trash2, Star } from 'lucide-react';
import type { Character, Persona } from '@/types';

export function CharacterPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { fetchChats } = useChatStore();
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showPersonaModal, setShowPersonaModal] = useState(false);
  const [personas, setPersonas] = useState<Persona[]>([]);

  const isAdmin = user?.role === 'admin';
  const isOwner = isAuthenticated && character && (user?.id === character.creator_id || isAdmin);

  const tpl = (text: string) =>
    text.replace(/\{\{char\}\}/g, character?.name || '').replace(/\{\{user\}\}/g, user?.username || 'User');

  useEffect(() => {
    if (id) {
      getCharacter(id).then(setCharacter);
    }
  }, [id]);

  const startChatWithPersona = async (personaId?: string) => {
    if (!character) return;
    setShowPersonaModal(false);
    setLoading(true);
    try {
      const { chat } = await createChat(character.id, undefined, personaId);
      await fetchChats();
      navigate(`/chat/${chat.id}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = async () => {
    if (!character || !isAuthenticated) {
      navigate('/auth');
      return;
    }
    // Fetch personas and decide flow
    try {
      const list = await getPersonas();
      setPersonas(list);
      if (list.length === 0) {
        // No personas — start directly
        startChatWithPersona();
      } else if (list.length === 1 && list[0].is_default) {
        // Single default persona — use automatically
        startChatWithPersona(list[0].id);
      } else {
        // Multiple personas — show picker
        setShowPersonaModal(true);
      }
    } catch {
      // API error — start without persona
      startChatWithPersona();
    }
  };

  const handleDelete = async () => {
    if (!character) return;
    setShowDeleteConfirm(false);
    setDeleting(true);
    try {
      await deleteCharacter(character.id);
      navigate('/');
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } }; message?: string };
      alert(ax?.response?.data?.detail || ax?.message || t('character.deleteError'));
      setDeleting(false);
    }
  };

  if (!character) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-neutral-500">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="relative min-h-full">
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
        <Avatar src={character.avatar_url} name={character.name} size="lg" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{character.name}</h1>
          {character.tagline && (
            <p className="text-neutral-400 mt-1">{character.tagline}</p>
          )}
          <div className="flex items-center gap-4 mt-3 text-sm text-neutral-500">
            <span className="flex items-center gap-1">
              <MessageCircle className="w-4 h-4" />
              {character.chat_count} {t('character.chats')}
            </span>
            <span className="flex items-center gap-1">
              <Heart className="w-4 h-4" />
              {character.like_count}
            </span>
            {character.profiles?.username && (
              <span className="flex items-center gap-1">
                <User className="w-4 h-4" />
                @{character.profiles.username}
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
      </div>

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

      <Button onClick={handleStartChat} disabled={loading} size="lg" className="w-full">
        {loading ? t('character.creatingChat') : t('character.startChat')}
      </Button>

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
                onClick={() => startChatWithPersona()}
                className="w-full text-left p-3 rounded-xl bg-neutral-800/50 border border-neutral-700 hover:border-neutral-500 transition-colors"
              >
                <span className="font-medium text-neutral-300">{t('persona.none')}</span>
                <span className="block text-xs text-neutral-500 mt-0.5">{t('persona.noneHint')}</span>
              </button>
              {/* Persona options */}
              {personas.map((p) => (
                <button
                  key={p.id}
                  onClick={() => startChatWithPersona(p.id)}
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
      </div>
    </div>
  );
}
