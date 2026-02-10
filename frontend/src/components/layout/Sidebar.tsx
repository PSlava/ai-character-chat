import { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useChatStore } from '@/store/chatStore';
import { useAuth } from '@/hooks/useAuth';
import { Avatar } from '@/components/ui/Avatar';
import { MessageCircle, Home, Heart, Settings } from 'lucide-react';

export function Sidebar() {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const isAdmin = user?.role === 'admin';
  const { chats, fetchChats } = useChatStore();
  const { chatId } = useParams();

  useEffect(() => {
    if (isAuthenticated) {
      fetchChats();
    }
  }, [isAuthenticated, fetchChats]);

  return (
    <aside className="w-64 border-r border-neutral-800 flex flex-col h-full overflow-hidden shrink-0 hidden md:flex">
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
            to="/profile"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
          >
            <Heart className="w-4 h-4" />
            {t('sidebar.favorites')}
          </Link>
        )}
        {isAdmin && (
          <Link
            to="/admin/prompts"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 text-neutral-300"
          >
            <Settings className="w-4 h-4" />
            {t('admin.prompts')}
          </Link>
        )}
      </nav>

      {isAuthenticated && chats.length > 0 && (
        <div className="flex-1 overflow-y-auto border-t border-neutral-800">
          <div className="p-3">
            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2 px-3">
              {t('sidebar.myChats')}
            </p>
            <div className="space-y-1">
              {chats.map((chat) => (
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
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {!isAuthenticated && (
        <div className="p-4 text-sm text-neutral-500">
          <MessageCircle className="w-8 h-8 mb-2 text-neutral-600" />
          <p>{t('sidebar.loginPrompt')}</p>
        </div>
      )}
    </aside>
  );
}
