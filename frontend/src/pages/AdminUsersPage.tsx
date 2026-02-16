import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { getAdminUsers, banUser, unbanUser, deleteUser, getAdminSettings, updateAdminSetting } from '@/api/admin';
import type { AdminUser } from '@/api/admin';
import { Avatar } from '@/components/ui/Avatar';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Search, Ban, ShieldCheck, Trash2, MessageCircle, MessagesSquare, Users, Bell, BellOff, DollarSign, MessageCircleWarning, UserCircle, UserPlus } from 'lucide-react';

export function AdminUsersPage() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [search, setSearch] = useState('');
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [notifyRegistration, setNotifyRegistration] = useState(true);
  const [paidMode, setPaidMode] = useState(false);
  const [dailyLimit, setDailyLimit] = useState('1000');
  const [editingLimit, setEditingLimit] = useState(false);
  const [maxPersonas, setMaxPersonas] = useState('5');
  const [editingPersonas, setEditingPersonas] = useState(false);
  const [anonLimit, setAnonLimit] = useState('50');
  const [editingAnonLimit, setEditingAnonLimit] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    getAdminUsers()
      .then(setUsers)
      .finally(() => setLoadingUsers(false));
    getAdminSettings()
      .then((s) => {
        setNotifyRegistration(s.notify_registration === 'true');
        setPaidMode(s.paid_mode === 'true');
        setDailyLimit(s.daily_message_limit || '1000');
        setMaxPersonas(s.max_personas || '5');
        setAnonLimit(s.anon_message_limit || '50');
      })
      .catch(() => {});
  }, [isAdmin]);

  const toggleNotify = async () => {
    const newVal = !notifyRegistration;
    setNotifyRegistration(newVal);
    try {
      await updateAdminSetting('notify_registration', newVal ? 'true' : 'false');
    } catch {
      setNotifyRegistration(!newVal);
    }
  };

  const togglePaidMode = async () => {
    const newVal = !paidMode;
    setPaidMode(newVal);
    try {
      await updateAdminSetting('paid_mode', newVal ? 'true' : 'false');
    } catch {
      setPaidMode(!newVal);
    }
  };

  const saveDailyLimit = async (val: string) => {
    const num = parseInt(val, 10);
    if (isNaN(num) || num < 0) return;
    setDailyLimit(String(num));
    setEditingLimit(false);
    try {
      await updateAdminSetting('daily_message_limit', String(num));
    } catch {
      // revert on error
    }
  };

  const saveMaxPersonas = async (val: string) => {
    const num = parseInt(val, 10);
    if (isNaN(num) || num < 0) return;
    setMaxPersonas(String(num));
    setEditingPersonas(false);
    try {
      await updateAdminSetting('max_personas', String(num));
    } catch {
      // revert on error
    }
  };

  const saveAnonLimit = async (val: string) => {
    const num = parseInt(val, 10);
    if (isNaN(num) || num < 0) return;
    setAnonLimit(String(num));
    setEditingAnonLimit(false);
    try {
      await updateAdminSetting('anon_message_limit', String(num));
    } catch {
      // revert on error
    }
  };

  const filtered = useMemo(() => {
    if (!search.trim()) return users;
    const q = search.toLowerCase();
    return users.filter(
      (u) =>
        u.email.toLowerCase().includes(q) ||
        u.username.toLowerCase().includes(q) ||
        (u.display_name && u.display_name.toLowerCase().includes(q))
    );
  }, [users, search]);

  const handleBan = async (userId: string) => {
    setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_banned: true } : u)));
    try {
      await banUser(userId);
    } catch {
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_banned: false } : u)));
    }
  };

  const handleUnban = async (userId: string) => {
    setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_banned: false } : u)));
    try {
      await unbanUser(userId);
    } catch {
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_banned: true } : u)));
    }
  };

  const handleDelete = async (userId: string) => {
    setConfirmDelete(null);
    try {
      await deleteUser(userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch {
      /* ignore */
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-neutral-500">{t('common.loading')}</div>
      </div>
    );
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString();
  };

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{t('admin.usersTitle')}</h1>
          <p className="text-neutral-400 text-sm mt-1">
            {users.length} {t('admin.usersTotal')}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <div className="relative">
            <button
              onClick={() => setEditingLimit(!editingLimit)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
              title={t('admin.dailyMessageLimitHint')}
            >
              <MessageCircleWarning className="w-4 h-4" />
              <span className="hidden sm:inline">{dailyLimit}</span>
            </button>
            {editingLimit && (
              <div className="absolute right-0 top-full mt-1 bg-neutral-800 border border-neutral-700 rounded-lg p-2 z-10 flex gap-2">
                <input
                  type="number"
                  min="0"
                  defaultValue={dailyLimit}
                  className="w-24 px-2 py-1 bg-neutral-900 border border-neutral-600 rounded text-sm text-white focus:outline-none focus:border-rose-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveDailyLimit((e.target as HTMLInputElement).value);
                    if (e.key === 'Escape') setEditingLimit(false);
                  }}
                  autoFocus
                />
                <button
                  onClick={(e) => {
                    const input = (e.currentTarget.parentElement as HTMLElement).querySelector('input');
                    if (input) saveDailyLimit(input.value);
                  }}
                  className="px-2 py-1 bg-rose-600 text-white text-xs rounded hover:bg-rose-700"
                >
                  OK
                </button>
              </div>
            )}
          </div>
          <div className="relative">
            <button
              onClick={() => setEditingPersonas(!editingPersonas)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
              title={t('admin.maxPersonasHint')}
            >
              <UserCircle className="w-4 h-4" />
              <span className="hidden sm:inline">{maxPersonas}</span>
            </button>
            {editingPersonas && (
              <div className="absolute right-0 top-full mt-1 bg-neutral-800 border border-neutral-700 rounded-lg p-2 z-10 flex gap-2">
                <input
                  type="number"
                  min="0"
                  defaultValue={maxPersonas}
                  className="w-24 px-2 py-1 bg-neutral-900 border border-neutral-600 rounded text-sm text-white focus:outline-none focus:border-rose-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveMaxPersonas((e.target as HTMLInputElement).value);
                    if (e.key === 'Escape') setEditingPersonas(false);
                  }}
                  autoFocus
                />
                <button
                  onClick={(e) => {
                    const input = (e.currentTarget.parentElement as HTMLElement).querySelector('input');
                    if (input) saveMaxPersonas(input.value);
                  }}
                  className="px-2 py-1 bg-rose-600 text-white text-xs rounded hover:bg-rose-700"
                >
                  OK
                </button>
              </div>
            )}
          </div>
          <div className="relative">
            <button
              onClick={() => setEditingAnonLimit(!editingAnonLimit)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
              title={t('admin.anonLimitHint')}
            >
              <UserPlus className="w-4 h-4" />
              <span className="hidden sm:inline">{anonLimit}</span>
            </button>
            {editingAnonLimit && (
              <div className="absolute right-0 top-full mt-1 bg-neutral-800 border border-neutral-700 rounded-lg p-2 z-10 flex gap-2">
                <input
                  type="number"
                  min="0"
                  defaultValue={anonLimit}
                  className="w-24 px-2 py-1 bg-neutral-900 border border-neutral-600 rounded text-sm text-white focus:outline-none focus:border-rose-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveAnonLimit((e.target as HTMLInputElement).value);
                    if (e.key === 'Escape') setEditingAnonLimit(false);
                  }}
                  autoFocus
                />
                <button
                  onClick={(e) => {
                    const input = (e.currentTarget.parentElement as HTMLElement).querySelector('input');
                    if (input) saveAnonLimit(input.value);
                  }}
                  className="px-2 py-1 bg-rose-600 text-white text-xs rounded hover:bg-rose-700"
                >
                  OK
                </button>
              </div>
            )}
          </div>
          <button
            onClick={togglePaidMode}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
              paidMode
                ? 'bg-green-900/30 text-green-400 hover:bg-green-900/50'
                : 'bg-neutral-800 text-neutral-500 hover:bg-neutral-700'
            }`}
            title={t('admin.paidModeHint')}
          >
            <DollarSign className="w-4 h-4" />
            <span className="hidden sm:inline">{t('admin.paidMode')}</span>
          </button>
          <button
            onClick={toggleNotify}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
              notifyRegistration
                ? 'bg-green-900/30 text-green-400 hover:bg-green-900/50'
                : 'bg-neutral-800 text-neutral-500 hover:bg-neutral-700'
            }`}
            title={t('admin.notifyRegistrationHint')}
          >
            {notifyRegistration ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
            <span className="hidden sm:inline">{t('admin.notifyRegistration')}</span>
          </button>
        </div>
      </div>

      <div className="relative mb-4 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('admin.userSearch')}
          className="w-full pl-10 pr-4 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-rose-500"
        />
      </div>

      {loadingUsers ? (
        <div className="text-neutral-500 text-sm">{t('common.loading')}</div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase tracking-wider">
                  <th className="text-left py-3 px-3">{t('admin.userCol')}</th>
                  <th className="text-left py-3 px-3">Email</th>
                  <th className="text-center py-3 px-3">{t('admin.roleCol')}</th>
                  <th className="text-center py-3 px-3"><MessageCircle className="w-3.5 h-3.5 inline" /></th>
                  <th className="text-center py-3 px-3"><MessagesSquare className="w-3.5 h-3.5 inline" /></th>
                  <th className="text-center py-3 px-3"><Users className="w-3.5 h-3.5 inline" /></th>
                  <th className="text-center py-3 px-3">{t('admin.langCol')}</th>
                  <th className="text-center py-3 px-3">{t('admin.dateCol')}</th>
                  <th className="text-center py-3 px-3">{t('admin.statusCol')}</th>
                  <th className="text-right py-3 px-3">{t('admin.actionsCol')}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id} className="border-b border-neutral-800/50 hover:bg-neutral-800/30">
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <Avatar src={u.avatar_url} name={u.display_name || u.username} size="sm" />
                        <div className="min-w-0">
                          <div className="text-white truncate">{u.display_name || u.username}</div>
                          <div className="text-neutral-500 text-xs">@{u.username}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-neutral-400">{u.email}</td>
                    <td className="py-3 px-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        u.role === 'admin'
                          ? 'bg-purple-900/30 text-purple-400'
                          : 'bg-neutral-800 text-neutral-400'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center text-neutral-400">{u.message_count}</td>
                    <td className="py-3 px-3 text-center text-neutral-400">{u.chat_count}</td>
                    <td className="py-3 px-3 text-center text-neutral-400">{u.character_count}</td>
                    <td className="py-3 px-3 text-center text-neutral-400 text-xs uppercase">{u.language}</td>
                    <td className="py-3 px-3 text-center text-neutral-500 text-xs">{formatDate(u.created_at)}</td>
                    <td className="py-3 px-3 text-center">
                      {u.is_banned ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/30 text-red-400">
                          {t('admin.banned')}
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400">
                          {t('admin.active')}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {u.id !== user?.id && (
                          <>
                            {u.is_banned ? (
                              <button
                                onClick={() => handleUnban(u.id)}
                                className="p-1.5 rounded-lg hover:bg-green-900/30 text-neutral-400 hover:text-green-400 transition-colors"
                                title={t('admin.unban')}
                              >
                                <ShieldCheck className="w-4 h-4" />
                              </button>
                            ) : (
                              <button
                                onClick={() => handleBan(u.id)}
                                className="p-1.5 rounded-lg hover:bg-amber-900/30 text-neutral-400 hover:text-amber-400 transition-colors"
                                title={t('admin.ban')}
                              >
                                <Ban className="w-4 h-4" />
                              </button>
                            )}
                            <button
                              onClick={() => setConfirmDelete(u.id)}
                              className="p-1.5 rounded-lg hover:bg-red-900/30 text-neutral-400 hover:text-red-400 transition-colors"
                              title={t('admin.deleteUser')}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {filtered.map((u) => (
              <div key={u.id} className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <Avatar src={u.avatar_url} name={u.display_name || u.username} size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium truncate">{u.display_name || u.username}</span>
                      {u.is_banned && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-900/30 text-red-400">
                          {t('admin.banned')}
                        </span>
                      )}
                      {u.role === 'admin' && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-900/30 text-purple-400">
                          admin
                        </span>
                      )}
                    </div>
                    <div className="text-neutral-500 text-xs">@{u.username}</div>
                    <div className="text-neutral-500 text-xs mt-0.5">{u.email}</div>
                    <div className="flex items-center gap-3 mt-2 text-xs text-neutral-500">
                      <span className="flex items-center gap-1">
                        <MessageCircle className="w-3 h-3" /> {u.message_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessagesSquare className="w-3 h-3" /> {u.chat_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" /> {u.character_count}
                      </span>
                      <span className="uppercase">{u.language}</span>
                      <span>{formatDate(u.created_at)}</span>
                    </div>
                  </div>
                  {u.id !== user?.id && (
                    <div className="flex gap-1 shrink-0">
                      {u.is_banned ? (
                        <button
                          onClick={() => handleUnban(u.id)}
                          className="p-1.5 rounded-lg hover:bg-green-900/30 text-neutral-400 hover:text-green-400 transition-colors"
                        >
                          <ShieldCheck className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleBan(u.id)}
                          className="p-1.5 rounded-lg hover:bg-amber-900/30 text-neutral-400 hover:text-amber-400 transition-colors"
                        >
                          <Ban className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => setConfirmDelete(u.id)}
                        className="p-1.5 rounded-lg hover:bg-red-900/30 text-neutral-400 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {confirmDelete && (
        <ConfirmDialog
          title={t('admin.deleteUserTitle')}
          message={t('admin.deleteUserConfirm')}
          onConfirm={() => handleDelete(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  );
}
