import type { Character } from '@/types';
import { CharacterCard } from './CharacterCard';

interface Props {
  characters: Character[];
  loading?: boolean;
}

export function CharacterGrid({ characters, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-neutral-800/50 rounded-xl p-4 h-32 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (characters.length === 0) {
    return (
      <div className="text-center py-12 text-neutral-500">
        Персонажи не найдены
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {characters.map((character) => (
        <CharacterCard key={character.id} character={character} />
      ))}
    </div>
  );
}
