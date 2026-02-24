import { useTranslation } from 'react-i18next';
import type { Character } from '@/types';
import { CharacterCard } from './CharacterCard';
import { Skeleton } from '@/components/ui/Skeleton';

interface Props {
  characters: Character[];
  loading?: boolean;
}

function SkeletonCard() {
  return (
    <div className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
      <div className="flex gap-3">
        <Skeleton className="w-12 h-12 rounded-full shrink-0" />
        <div className="flex-1 min-w-0 space-y-2">
          <Skeleton className="h-4 w-24 rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-2/3 rounded" />
        </div>
      </div>
      <div className="flex gap-3 mt-3">
        <Skeleton className="h-3 w-14 rounded" />
        <Skeleton className="h-3 w-10 rounded" />
      </div>
      <div className="flex gap-1.5 mt-3">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-12 rounded-full" />
      </div>
    </div>
  );
}

export function CharacterGrid({ characters, loading }: Props) {
  const { t } = useTranslation();
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (characters.length === 0) {
    return (
      <div className="text-center py-12 text-neutral-500">
        {t('home.noCharacters')}
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
