import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCharacter, deleteCharacter } from '@/api/characters';
import { createChat } from '@/api/chat';
import { useAuth } from '@/hooks/useAuth';
import { useChatStore } from '@/store/chatStore';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { MessageCircle, Heart, User, Pencil, Trash2 } from 'lucide-react';
import type { Character } from '@/types';

export function CharacterPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { fetchChats } = useChatStore();
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isOwner = isAuthenticated && character && user?.id === character.creator_id;

  useEffect(() => {
    if (id) {
      getCharacter(id).then(setCharacter);
    }
  }, [id]);

  const handleStartChat = async () => {
    if (!character || !isAuthenticated) {
      navigate('/auth');
      return;
    }
    setLoading(true);
    try {
      const { chat } = await createChat(character.id);
      await fetchChats();
      navigate(`/chat/${chat.id}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!character || !confirm('Удалить персонажа? Это действие нельзя отменить.')) return;
    setDeleting(true);
    try {
      await deleteCharacter(character.id);
      navigate('/');
    } catch {
      setDeleting(false);
    }
  };

  if (!character) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-neutral-500">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-start gap-6 mb-8">
        <Avatar src={character.avatar_url} name={character.name} size="lg" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{character.name}</h1>
          {character.tagline && (
            <p className="text-neutral-400 mt-1">{character.tagline}</p>
          )}
          <div className="flex items-center gap-4 mt-3 text-sm text-neutral-500">
            <span className="flex items-center gap-1">
              <MessageCircle className="w-4 h-4" />
              {character.chat_count} чатов
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
              title="Редактировать"
            >
              <Pencil className="w-4 h-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="p-2 rounded-lg bg-neutral-800 hover:bg-red-900/50 text-neutral-400 hover:text-red-400 transition-colors"
              title="Удалить"
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
            Сценарий
          </h2>
          <p className="text-neutral-200 bg-neutral-800/50 rounded-xl p-4">
            {character.scenario}
          </p>
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-sm font-medium text-neutral-400 mb-2 uppercase tracking-wider">
          Приветствие
        </h2>
        <div className="bg-neutral-800/50 rounded-xl p-4 text-neutral-200">
          {character.greeting_message}
        </div>
      </div>

      <Button onClick={handleStartChat} disabled={loading} size="lg" className="w-full">
        {loading ? 'Создание чата...' : 'Начать общение'}
      </Button>
    </div>
  );
}
