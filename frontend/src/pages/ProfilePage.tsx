import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getMyCharacters } from '@/api/characters';
import { getProfile, updateProfile } from '@/api/users';
import type { UserProfile } from '@/api/users';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';
import { useAuth } from '@/hooks/useAuth';
import type { Character } from '@/types';

export function ProfilePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [myCharacters, setMyCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getMyCharacters()
      .then(setMyCharacters)
      .finally(() => setLoading(false));
    getProfile().then((p) => {
      setProfile(p);
      setDisplayName(p.display_name || '');
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const updated = await updateProfile({ display_name: displayName || undefined });
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">{t('profile.title')}</h1>
        <p className="text-neutral-400 mt-1">{user?.email}</p>
      </div>

      <div className="mb-8 max-w-md">
        <h2 className="text-lg font-semibold mb-4">{t('profile.settings')}</h2>
        <div className="space-y-4">
          <Input
            label={t('profile.nameLabel')}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder={t('profile.namePlaceholder')}
          />
          <div className="flex items-center gap-3">
            <Button
              onClick={handleSave}
              disabled={saving || displayName === (profile?.display_name || '')}
            >
              {saving ? t('common.saving') : t('common.save')}
            </Button>
            {saved && (
              <span className="text-sm text-green-400">{t('common.saved')}</span>
            )}
          </div>
        </div>
      </div>

      <div className="mb-8 max-w-md">
        <div>
          <label className="block text-sm text-neutral-400 mb-1">{t('profile.language')}</label>
          <LanguageSwitcher />
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">{t('profile.myCharacters')}</h2>
        <CharacterGrid characters={myCharacters} loading={loading} />
      </div>
    </div>
  );
}
