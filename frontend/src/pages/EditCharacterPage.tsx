import { useState, useEffect } from 'react';
import { useParams, useNavigate, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCharacter, updateCharacter } from '@/api/characters';
import { CharacterForm } from '@/components/characters/CharacterForm';
import { LoreEditor } from '@/components/characters/LoreEditor';
import { localePath } from '@/lib/lang';
import type { Character } from '@/types';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';

export function EditCharacterPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const authUser = useAuthStore((s) => s.user);
  const isAdmin = authUser?.role === 'admin';
  const [character, setCharacter] = useState<Character | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      getCharacter(id)
        .then(setCharacter)
        .catch(() => setError(t('character.notFound')));
    }
  }, [id]);

  const handleSubmit = async (data: Partial<Character>) => {
    if (!id) return;
    try {
      const updated = await updateCharacter(id, data);
      navigate(localePath(updated.slug ? `/c/${updated.slug}` : `/character/${id}`));
    } catch {
      setError(t('edit.saveError'));
    }
  };

  if (!authLoading && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }

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
        <div className="animate-pulse text-neutral-500">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">{t('edit.title')}</h1>
      <CharacterForm
        initial={character}
        onSubmit={handleSubmit}
        submitLabel={t('edit.saveChanges')}
        isAdmin={isAdmin}
      />

      {/* Lorebook / World Info */}
      <div className="mt-8 border-t border-neutral-800 pt-6">
        <LoreEditor characterId={character.id} />
      </div>
    </div>
  );
}
