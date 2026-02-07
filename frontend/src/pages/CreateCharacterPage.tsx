import { useNavigate } from 'react-router-dom';
import { createCharacter } from '@/api/characters';
import { CharacterForm } from '@/components/characters/CharacterForm';
import type { Character } from '@/types';

export function CreateCharacterPage() {
  const navigate = useNavigate();

  const handleSubmit = async (data: Partial<Character>) => {
    const character = await createCharacter(data);
    navigate(`/character/${character.id}`);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Создать персонажа</h1>
      <CharacterForm onSubmit={handleSubmit} submitLabel="Создать персонажа" />
    </div>
  );
}
