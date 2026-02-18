import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useNavigate } from 'react-router-dom';
import { getMyCharacters } from '@/api/characters';
import { getProfile, updateProfile, deleteAccount } from '@/api/users';
import type { UserProfile } from '@/api/users';
import { getPersonas, createPersona, updatePersona, deletePersona, getPersonaLimit, checkPersonaSlug } from '@/api/personas';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { Input, Textarea } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AvatarUpload } from '@/components/ui/AvatarUpload';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';
import { SEO } from '@/components/seo/SEO';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';
import type { Character, Persona } from '@/types';
import { Plus, Star, Pencil, Trash2, Check, X, MessageCircle, MessagesSquare } from 'lucide-react';

export function ProfilePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
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

  // Personas state
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [showPersonaForm, setShowPersonaForm] = useState(false);
  const [editingPersona, setEditingPersona] = useState<Persona | null>(null);
  const [personaName, setPersonaName] = useState('');
  const [personaSlug, setPersonaSlug] = useState('');
  const [slugStatus, setSlugStatus] = useState<'idle' | 'checking' | 'available' | 'taken' | 'error'>('idle');
  const slugTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const [personaDesc, setPersonaDesc] = useState('');
  const [personaDefault, setPersonaDefault] = useState(false);
  const [personaSaving, setPersonaSaving] = useState(false);
  const [deletePersonaId, setDeletePersonaId] = useState<string | null>(null);
  const [personaLimit, setPersonaLimit] = useState(5);

  useEffect(() => {
    if (!isAuthenticated) return;
    getMyCharacters()
      .then(setMyCharacters)
      .finally(() => setLoading(false));
    getProfile().then((p) => {
      setProfile(p);
      setDisplayName(p.display_name || '');
      setUsername(p.username || '');
    });
    getPersonas().then(setPersonas).catch(() => {});
    getPersonaLimit().then((r) => setPersonaLimit(r.limit)).catch(() => {});
  }, [isAuthenticated]);

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

  const checkSlugAvailability = useCallback((slug: string) => {
    clearTimeout(slugTimerRef.current);
    const clean = slug.toLowerCase().replace(/[^a-z0-9-]/g, '');
    if (clean.length < 3) {
      setSlugStatus('idle');
      return;
    }
    setSlugStatus('checking');
    slugTimerRef.current = setTimeout(async () => {
      try {
        const result = await checkPersonaSlug(clean);
        setSlugStatus(result.available ? 'available' : 'taken');
      } catch {
        setSlugStatus('error');
      }
    }, 500);
  }, []);

  const resetPersonaForm = () => {
    setShowPersonaForm(false);
    setEditingPersona(null);
    setPersonaName('');
    setPersonaSlug('');
    setSlugStatus('idle');
    setPersonaDesc('');
    setPersonaDefault(false);
  };

  const handlePersonaSave = async () => {
    if (!personaName.trim()) return;
    setPersonaSaving(true);
    try {
      if (editingPersona) {
        const updated = await updatePersona(editingPersona.id, {
          name: personaName.trim(),
          slug: personaSlug.trim() || '',
          description: personaDesc.trim() || undefined,
          is_default: personaDefault,
        });
        setPersonas((prev) => prev.map((p) => {
          if (p.id === updated.id) return updated;
          if (personaDefault && p.is_default) return { ...p, is_default: false };
          return p;
        }));
      } else {
        const created = await createPersona({
          name: personaName.trim(),
          slug: personaSlug.trim() || undefined,
          description: personaDesc.trim() || undefined,
          is_default: personaDefault,
        });
        setPersonas((prev) => {
          const list = personaDefault ? prev.map((p) => ({ ...p, is_default: false })) : prev;
          return [...list, created];
        });
      }
      resetPersonaForm();
    } catch {
      /* ignore */
    } finally {
      setPersonaSaving(false);
    }
  };

  const handlePersonaDelete = async (id: string) => {
    setDeletePersonaId(null);
    try {
      await deletePersona(id);
      setPersonas((prev) => prev.filter((p) => p.id !== id));
    } catch { /* ignore */ }
  };

  const startEditPersona = (p: Persona) => {
    setEditingPersona(p);
    setPersonaName(p.name);
    setPersonaSlug(p.slug || '');
    setSlugStatus('idle');
    setPersonaDesc(p.description || '');
    setPersonaDefault(p.is_default);
    setShowPersonaForm(true);
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
        const detail = axiosErr.response?.data?.detail || '';
        const map: Record<string, string> = {
          'Username already taken': 'auth.usernameTaken',
          'Username must be 3-20 characters: letters, digits, underscore': 'auth.usernameInvalid',
        };
        const key = map[detail];
        setUsernameError(key ? t(key) : detail || t('auth.error'));
      }
    } finally {
      setSaving(false);
    }
  };

  if (!authLoading && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <SEO title={t('profile.title')} />
      <div className="mb-8">
        <h1 className="text-2xl font-bold">{t('profile.title')}</h1>
        <p className="text-neutral-400 mt-1">{user?.email}</p>
        {profile && (
          <div className="flex items-center gap-4 mt-3 text-sm text-neutral-400">
            <span className="flex items-center gap-1.5">
              <MessageCircle className="w-4 h-4" />
              {profile.message_count} {t('profile.messages')}
            </span>
            <span className="flex items-center gap-1.5">
              <MessagesSquare className="w-4 h-4" />
              {profile.chat_count} {t('profile.chats')}
            </span>
          </div>
        )}
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
              maxLength={20}
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
            maxLength={50}
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

      {/* Personas section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">{t('persona.title')}</h2>
            <p className="text-neutral-500 text-sm mt-0.5">{t('persona.subtitle')}</p>
          </div>
          {(personaLimit === 0 || personas.length < personaLimit) && !showPersonaForm && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => { resetPersonaForm(); setShowPersonaForm(true); }}
            >
              <Plus className="w-4 h-4 mr-1 inline" />
              {t('persona.create')}
            </Button>
          )}
        </div>

        {/* Inline form for create/edit */}
        {showPersonaForm && (
          <div className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-4 mb-4 max-w-md">
            <div className="space-y-3">
              <Input
                label={t('persona.name')}
                value={personaName}
                onChange={(e) => setPersonaName(e.target.value)}
                placeholder={t('persona.namePlaceholder')}
                maxLength={50}
              />
              <div>
                <Input
                  label={t('persona.slug')}
                  value={personaSlug}
                  onChange={(e) => {
                    const v = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '');
                    setPersonaSlug(v);
                    checkSlugAvailability(v);
                  }}
                  placeholder={t('persona.slugPlaceholder')}
                  maxLength={50}
                />
                <div className="mt-1 text-xs">
                  {slugStatus === 'checking' && <span className="text-neutral-500">{t('persona.slugChecking')}</span>}
                  {slugStatus === 'available' && <span className="text-green-400">{t('persona.slugAvailable')}</span>}
                  {slugStatus === 'taken' && <span className="text-red-400">{t('persona.slugTaken')}</span>}
                </div>
                <p className="text-xs text-neutral-500 mt-0.5">{t('persona.slugHint')}</p>
              </div>
              <Textarea
                label={t('persona.description')}
                value={personaDesc}
                onChange={(e) => setPersonaDesc(e.target.value)}
                placeholder={t('persona.descriptionPlaceholder')}
                rows={3}
                maxLength={2000}
              />
              <label className="flex items-center gap-2 cursor-pointer text-sm text-neutral-300">
                <input
                  type="checkbox"
                  checked={personaDefault}
                  onChange={(e) => setPersonaDefault(e.target.checked)}
                  className="rounded bg-neutral-700 border-neutral-600 text-rose-500 focus:ring-rose-500"
                />
                {t('persona.isDefault')}
              </label>
              <div className="flex gap-2">
                <Button size="sm" onClick={handlePersonaSave} disabled={personaSaving || !personaName.trim()}>
                  <Check className="w-4 h-4 mr-1 inline" />
                  {personaSaving ? t('common.saving') : t('common.save')}
                </Button>
                <Button variant="ghost" size="sm" onClick={resetPersonaForm}>
                  <X className="w-4 h-4 mr-1 inline" />
                  {t('common.cancel')}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Persona cards */}
        {personas.length === 0 && !showPersonaForm ? (
          <p className="text-neutral-500 text-sm">{t('persona.empty')}</p>
        ) : (
          <div className="grid gap-3 max-w-md">
            {personas.map((p) => (
              <div key={p.id} className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-4 flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white truncate">{p.name}</span>
                    {p.is_default && (
                      <span className="flex items-center gap-1 text-xs text-amber-400 bg-amber-900/30 px-2 py-0.5 rounded-full">
                        <Star className="w-3 h-3" />
                        {t('persona.default')}
                      </span>
                    )}
                  </div>
                  {p.description && (
                    <p className="text-neutral-400 text-sm mt-1 line-clamp-2">{p.description}</p>
                  )}
                </div>
                <div className="flex gap-1 shrink-0">
                  <button
                    onClick={() => startEditPersona(p)}
                    className="p-1.5 rounded-lg hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setDeletePersonaId(p.id)}
                    className="p-1.5 rounded-lg hover:bg-red-900/50 text-neutral-400 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {personaLimit > 0 && personas.length >= personaLimit && (
          <p className="text-neutral-500 text-xs mt-2">{t('persona.limit')}</p>
        )}
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

      {deletePersonaId && (
        <ConfirmDialog
          title={t('persona.deleteTitle')}
          message={t('persona.deleteConfirm')}
          onConfirm={() => handlePersonaDelete(deletePersonaId)}
          onCancel={() => setDeletePersonaId(null)}
        />
      )}

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
