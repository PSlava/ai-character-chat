import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getMyCharacters } from '@/api/characters';
import { getProfile, updateProfile, deleteAccount } from '@/api/users';
import type { UserProfile } from '@/api/users';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AvatarUpload } from '@/components/ui/AvatarUpload';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';
import type { Character } from '@/types';

export function ProfilePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const logout = useAuthStore((s) => s.logout);
  const [myCharacters, setMyCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [username, setUsername] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    getMyCharacters()
      .then(setMyCharacters)
      .finally(() => setLoading(false));
    getProfile().then((p) => {
      setProfile(p);
      setDisplayName(p.display_name || '');
      setUsername(p.username || '');
    });
  }, []);

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
      logout();
      navigate('/');
    } catch {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setUsernameError('');
    try {
      const body: Record<string, string | undefined> = { display_name: displayName || undefined };
      if (username !== (profile?.username || '')) {
        body.username = username;
      }
      const updated = await updateProfile(body);
      setProfile(updated);
      setUsername(updated.username || '');
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setUsernameError(axiosErr.response?.data?.detail || t('auth.error'));
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">{t('profile.title')}</h1>
        <p className="text-neutral-400 mt-1">{user?.email}</p>
      </div>

      <div className="mb-8 max-w-md">
        <h2 className="text-lg font-semibold mb-4">{t('profile.settings')}</h2>
        <div className="space-y-4">
          <AvatarUpload
            currentUrl={profile?.avatar_url || null}
            name={profile?.display_name || profile?.username || '?'}
            onChange={async (url) => {
              try {
                const updated = await updateProfile({ avatar_url: url });
                setProfile(updated);
              } catch { /* ignore */ }
            }}
          />
          <div>
            <Input
              label={t('profile.usernameLabel')}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t('profile.usernamePlaceholder')}
            />
            {usernameError && (
              <p className="text-red-400 text-xs mt-1">{usernameError}</p>
            )}
            <p className="text-neutral-500 text-xs mt-1">{t('profile.usernameHint')}</p>
          </div>
          <Input
            label={t('profile.nameLabel')}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder={t('profile.namePlaceholder')}
          />
          <div className="flex items-center gap-3">
            <Button
              onClick={handleSave}
              disabled={saving || (displayName === (profile?.display_name || '') && username === (profile?.username || ''))}
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

      <div className="mb-8 max-w-md border-t border-neutral-800 pt-6">
        <h2 className="text-lg font-semibold mb-2 text-red-400">{t('profile.dangerZone')}</h2>
        <p className="text-neutral-400 text-sm mb-4">{t('profile.deleteAccountHint')}</p>
        <Button
          variant="danger"
          onClick={() => setShowDeleteConfirm(true)}
        >
          {t('profile.deleteAccount')}
        </Button>
      </div>

      {showDeleteConfirm && (
        <ConfirmDialog
          title={t('profile.deleteAccountTitle')}
          message={t('profile.deleteAccountConfirm')}
          confirmLabel={deleting ? t('profile.deleting') : t('common.delete')}
          onConfirm={handleDeleteAccount}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}
    </div>
  );
}
