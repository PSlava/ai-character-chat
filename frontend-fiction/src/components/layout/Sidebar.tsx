import { useEffect, useMemo } from 'react';
import { Link, useParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useChatStore } from '@/store/chatStore';
import { useFavoritesStore } from '@/store/favoritesStore';
import { useVotesStore } from '@/store/votesStore';
import { useAuth } from '@/hooks/useAuth';
import { Avatar } from '@/components/ui/Avatar';
import { Logo } from '@/components/ui/Logo';
import { Home, Heart, Settings, Users, BarChart3, X, Sparkles, Swords } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: Props) {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const isAdmin = user?.role === 'admin';
  const { chats, loading: chatsLoading, fetchChats } = useChatStore();
  const { fetchFavorites } = useFavoritesStore();
  const { fetchVotes } = useVotesStore();
  const { chatId } = useParams();
  const location = useLocation();

  useEffect(() => {
    if (isAuthenticated) {
      fetchChats();
      fetchFavorites();
      fetchVotes();
    }
  }, [isAuthenticated, fetchChats, fetchFavorites, fetchVotes]);

  // Close drawer on route change (mobile)
  useEffect(() => {
    onClose();
  }, [location.pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  // Memoize chat grouping to avoid re-computing on every render
  const groupedChats = useMemo(() => {
    const grouped = new Map<string, typeof chats>();
    for (const chat of chats) {
      const key = chat.character_id;
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key)!.push(chat);
    }
    return Array.from(grouped.values());
  }, [chats]);

  const sidebarContent = (
    <>
      <nav className="p-3 space-y-1">
        <Link
          to="/"
          className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
        >
          <Home className="w-4 h-4" />
          {t('sidebar.home')}
        </Link>
        {isAuthenticated && (
          <Link
            to="/favorites"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
          >
            <Heart className="w-4 h-4" />
            {t('sidebar.favorites')}
          </Link>
        )}
        {isAuthenticated && (
          <Link
            to="/profile?tab=characters"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
          >
            <Sparkles className="w-4 h-4" />
            {t('sidebar.myCharacters')}
          </Link>
        )}
        {isAuthenticated && (
          <Link
            to="/campaigns"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
          >
            <Swords className="w-4 h-4" />
            {t('game.campaigns', 'Campaigns')}
          </Link>
        )}
        {isAdmin && (
          <>
            <Link
              to="/admin/users"
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
            >
              <Users className="w-4 h-4" />
              {t('admin.users')}
            </Link>
            <Link
              to="/admin/prompts"
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
            >
              <Settings className="w-4 h-4" />
              {t('admin.prompts')}
            </Link>
            <Link
              to="/admin/analytics"
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
            >
              <BarChart3 className="w-4 h-4" />
              {t('admin.analytics')}
            </Link>
          </>
        )}
      </nav>

      {isAuthenticated && (chatsLoading || chats.length > 0) && (
        <div className="flex-1 overflow-y-auto border-t border-neutral-800">
          <div className="p-3">
            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2 px-3">
              {t('sidebar.myChats')}
            </p>
            {chatsLoading && chats.length === 0 ? (
              <div className="space-y-1">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-2 px-3 py-2">
                    <div className="w-8 h-8 rounded-full animate-pulse bg-neutral-700/50 shrink-0" />
                    <div className="h-4 rounded animate-pulse bg-neutral-700/50 flex-1" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-1">
                {groupedChats.flatMap((group) =>
                  group.map((chat, idx) => (
                    <Link
                      key={chat.id}
                      to={`/chat/${chat.id}`}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                        chatId === chat.id
                          ? 'bg-purple-600/20 text-purple-300'
                          : 'hover:bg-neutral-800 text-neutral-400'
                      }`}
                    >
                      <Avatar
                        src={chat.characters?.avatar_url}
                        name={chat.characters?.name || '?'}
                        size="sm"
                      />
                      <span className="truncate">
                        {chat.characters?.name || chat.title}
                        {group.length > 1 && ` #${idx + 1}`}
                      </span>
                    </Link>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {!isAuthenticated && (
        <div className="p-4 text-sm text-neutral-500">
          <Logo className="w-8 h-8 mb-2 text-neutral-600" />
          <p>{t('sidebar.loginPrompt')}</p>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="w-64 border-r border-neutral-800 flex-col h-full overflow-hidden shrink-0 hidden md:flex">
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/50" onClick={onClose} />
          {/* Panel */}
          <aside className="relative w-64 h-full bg-neutral-900 border-r border-neutral-800 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b border-neutral-800">
              <span className="text-sm font-semibold flex items-center gap-1">
                <Logo className="w-5 h-5 text-purple-500" />
                <span className="text-neutral-300">Grim</span><span className="text-purple-500">Quill</span>
              </span>
              <button onClick={onClose} className="p-1 text-neutral-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
