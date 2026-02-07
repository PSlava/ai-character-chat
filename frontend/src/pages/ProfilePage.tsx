import { useState, useEffect } from 'react';
import { getMyCharacters } from '@/api/characters';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { useAuth } from '@/hooks/useAuth';
import type { Character } from '@/types';

export function ProfilePage() {
  const { user } = useAuth();
  const [myCharacters, setMyCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyCharacters()
      .then(setMyCharacters)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Профиль</h1>
        <p className="text-neutral-400 mt-1">{user?.email}</p>
      </div>

      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Мои персонажи</h2>
        <CharacterGrid characters={myCharacters} loading={loading} />
      </div>
    </div>
  );
}
