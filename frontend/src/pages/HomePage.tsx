import { useState, useEffect } from 'react';
import { getCharacters } from '@/api/characters';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { Input } from '@/components/ui/Input';
import { Search } from 'lucide-react';
import type { Character } from '@/types';

export function HomePage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      getCharacters({ search: search || undefined })
        .then(setCharacters)
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Персонажи</h1>
        <p className="text-neutral-400">
          Выберите персонажа и начните общение
        </p>
      </div>

      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск персонажей..."
          className="w-full bg-neutral-800 border border-neutral-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder-neutral-500 focus:outline-none focus:border-purple-500"
        />
      </div>

      <CharacterGrid characters={characters} loading={loading} />
    </div>
  );
}
