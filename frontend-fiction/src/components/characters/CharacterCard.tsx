import { useRef, memo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { Character } from '@/types';
import { Avatar } from '@/components/ui/Avatar';
import { useAuth } from '@/hooks/useAuth';
import { useFavoritesStore } from '@/store/favoritesStore';
import { useVotesStore } from '@/store/votesStore';
import { isCharacterOnline } from '@/lib/utils';
import { localePath } from '@/lib/lang';
import { MessageCircle, Heart, ThumbsUp, ThumbsDown, GitFork } from 'lucide-react';

interface Props {
  character: Character;
}

export const CharacterCard = memo(function CharacterCard({ character }: Props) {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const { favoriteIds, addFavorite, removeFavorite } = useFavoritesStore();
  const { votes, vote } = useVotesStore();
  const isFav = favoriteIds.has(character.id);
  const initialFav = useRef(isFav);
  const likeOffset = (isFav ? 1 : 0) - (initialFav.current ? 1 : 0);
  const userVote = votes[character.id] || 0;
  const [scoreOffset, setScoreOffset] = useState(0);

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

  const handleVote = async (e: React.MouseEvent, value: number) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) { navigate('/auth'); return; }
    const newValue = userVote === value ? 0 : value;
    const result = await vote(character.id, newValue);
    if (result) {
      setScoreOffset(result.vote_score - (character.vote_score || 0));
    }
  };

  return (
    <Link
      to={localePath(character.slug ? `/c/${character.slug}` : `/character/${character.id}`)}
      className="block bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4 hover:border-purple-500/50 transition-all hover:bg-neutral-800"
    >
      <div className="flex items-start gap-3">
        <div className="relative shrink-0">
          <Avatar src={character.avatar_url} name={character.name} size="lg" />
          {isCharacterOnline(character.id) && (
            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-neutral-800" />
          )}
        </div>
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
              {isAdmin && character.real_chat_count !== undefined && (
                <span className="text-emerald-500/70">({character.real_chat_count})</span>
              )}
            </span>
            <button
              onClick={toggleFavorite}
              className={`flex items-center gap-1 transition-colors ${
                isFav
                  ? 'text-purple-500 hover:text-purple-400'
                  : 'hover:text-purple-400'
              }`}
            >
              <Heart className={`w-3 h-3 ${isFav ? 'fill-current' : ''}`} />
              {Math.max(0, character.like_count + likeOffset)}
              {isAdmin && character.real_like_count !== undefined && (
                <span className="text-emerald-500/70">({character.real_like_count})</span>
              )}
            </button>
            <span className="flex items-center gap-0.5">
              <button onClick={(e) => handleVote(e, 1)} className={`transition-colors ${userVote === 1 ? 'text-green-400' : 'hover:text-green-400'}`}>
                <ThumbsUp className={`w-3 h-3 ${userVote === 1 ? 'fill-current' : ''}`} />
              </button>
              <span className={(character.vote_score || 0) + scoreOffset > 0 ? 'text-green-400' : (character.vote_score || 0) + scoreOffset < 0 ? 'text-red-400' : ''}>
                {(character.vote_score || 0) + scoreOffset}
              </span>
              <button onClick={(e) => handleVote(e, -1)} className={`transition-colors ${userVote === -1 ? 'text-red-400' : 'hover:text-red-400'}`}>
                <ThumbsDown className={`w-3 h-3 ${userVote === -1 ? 'fill-current' : ''}`} />
              </button>
            </span>
            {(character.fork_count || 0) > 0 && (
              <span className="flex items-center gap-1">
                <GitFork className="w-3 h-3" />
                {character.fork_count}
              </span>
            )}
          </div>
        </div>
      </div>
      {character.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
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
    </Link>
  );
});
