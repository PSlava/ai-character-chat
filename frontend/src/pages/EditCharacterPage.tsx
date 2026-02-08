import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCharacter, updateCharacter } from '@/api/characters';
import { CharacterForm } from '@/components/characters/CharacterForm';
import type { Character } from '@/types';

export function EditCharacterPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [character, setCharacter] = useState<Character | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      getCharacter(id)
        .then(setCharacter)
        .catch(() => setError('Персонаж не найден'));
    }
  }, [id]);

  const handleSubmit = async (data: Partial<Character>) => {
    if (!id) return;
    try {
      await updateCharacter(id, data);
      navigate(`/character/${id}`);
    } catch {
      setError('Не удалось сохранить изменения');
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400">
        {error}
      </div>
    );
  }

  if (!character) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-neutral-500">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Редактировать персонажа</h1>
      <CharacterForm
        initial={character}
        onSubmit={handleSubmit}
        submitLabel="Сохранить изменения"
      />
    </div>
  );
}
