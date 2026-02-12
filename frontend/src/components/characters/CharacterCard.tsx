import { useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { Character } from '@/types';
import { Avatar } from '@/components/ui/Avatar';
import { useAuth } from '@/hooks/useAuth';
import { useFavoritesStore } from '@/store/favoritesStore';
import { MessageCircle, Heart } from 'lucide-react';

interface Props {
  character: Character;
}

export function CharacterCard({ character }: Props) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { favoriteIds, addFavorite, removeFavorite } = useFavoritesStore();
  const isFav = favoriteIds.has(character.id);
  const initialFav = useRef(isFav);
  const likeOffset = (isFav ? 1 : 0) - (initialFav.current ? 1 : 0);

  const toggleFavorite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      navigate('/auth');
      return;
    }
    if (isFav) {
      removeFavorite(character.id);
    } else {
      addFavorite(character.id);
    }
  };

  return (
    <Link
      to={`/character/${character.id}`}
      className="block bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4 hover:border-rose-500/50 transition-all hover:bg-neutral-800"
    >
      <div className="flex items-start gap-3">
        <Avatar src={character.avatar_url} name={character.name} size="lg" />
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white truncate">{character.name}</h3>
          {character.tagline && (
            <p className="text-sm text-neutral-400 mt-1 line-clamp-2">
              {character.tagline}
            </p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-neutral-500">
            <span className="flex items-center gap-1">
              <MessageCircle className="w-3 h-3" />
              {character.chat_count}
            </span>
            <button
              onClick={toggleFavorite}
              className={`flex items-center gap-1 transition-colors ${
                isFav
                  ? 'text-rose-500 hover:text-rose-400'
                  : 'hover:text-rose-400'
              }`}
            >
              <Heart className={`w-3 h-3 ${isFav ? 'fill-current' : ''}`} />
              {Math.max(0, character.like_count + likeOffset)}
            </button>
            {character.profiles?.username && (
              <span>@{character.profiles.username}</span>
            )}
          </div>
          {character.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {character.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-neutral-700 rounded-full text-xs text-neutral-300"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
