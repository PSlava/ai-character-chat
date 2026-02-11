import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Trash2, RefreshCw, EllipsisVertical } from 'lucide-react';
import type { Message } from '@/types';
import { Avatar } from '@/components/ui/Avatar';

interface Props {
  message: Message;
  characterName?: string;
  characterAvatar?: string | null;
  isFirstMessage?: boolean;
  isAdmin?: boolean;
  onDelete?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
}

export function MessageBubble({ message, characterName, characterAvatar, isFirstMessage, isAdmin, onDelete, onRegenerate }: Props) {
  const { t } = useTranslation();
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const canRegenerate = isAssistant && !isFirstMessage && !!onRegenerate;
  const canDelete = !isFirstMessage && !!onDelete;
  const hasMenu = canDelete; // menu contains delete (and potentially more later)

  // Close menu on outside click/tap
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent | TouchEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    document.addEventListener('touchstart', handler);
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('touchstart', handler);
    };
  }, [menuOpen]);

  return (
    <div>
      {/* Header: avatar + name + action buttons */}
      <div className={`flex items-center gap-2.5 mb-1 ${isUser ? 'flex-row-reverse' : ''}`}>
        {isUser ? (
          <Avatar name={t('chat.you')} size="sm" />
        ) : (
          <Avatar src={characterAvatar} name={characterName || 'AI'} size="sm" />
        )}
        <span className="text-sm font-medium text-neutral-300">
          {isUser ? t('chat.you') : characterName}
        </span>

        {/* Action buttons — right side (or left for user messages) */}
        {!isFirstMessage && (
          <div className={`flex items-center gap-0.5 ${isUser ? 'mr-auto' : 'ml-auto'}`}>
            {canRegenerate && (
              <button
                onClick={() => onRegenerate!(message.id)}
                className="flex items-center gap-1.5 px-2 py-1 text-neutral-500 hover:text-neutral-300 rounded-md transition-colors"
              >
                <RefreshCw size={14} />
                <span className="hidden sm:inline text-xs">{t('chat.regenerate')}</span>
              </button>
            )}
            {hasMenu && (
              <div ref={menuRef} className="relative">
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="p-1.5 text-neutral-500 hover:text-neutral-300 rounded-md transition-colors"
                >
                  <EllipsisVertical size={16} />
                </button>
                {menuOpen && (
                  <div
                    className={`absolute z-50 top-full mt-1 py-1 bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl min-w-[160px] ${
                      isUser ? 'left-0' : 'right-0'
                    }`}
                  >
                    {canDelete && (
                      <button
                        onClick={() => { onDelete!(message.id); setMenuOpen(false); }}
                        className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-700 hover:text-red-400 transition-colors"
                      >
                        <Trash2 size={14} />
                        {t('chat.deleteMessage')}
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Message bubble */}
      <div
        className={`rounded-2xl px-4 py-2.5 ${
          isUser
            ? `ml-auto max-w-[85%] sm:max-w-[75%] ${
                message.isError
                  ? 'bg-red-900/30 border border-red-800 text-red-300'
                  : 'bg-purple-600 text-white'
              }`
            : `${
                message.isError
                  ? 'bg-red-900/30 border border-red-800 text-red-300'
                  : 'bg-neutral-800 text-neutral-100'
              }`
        }`}
      >
        <p className="whitespace-pre-wrap break-words">
          {message.content || (isAssistant ? '...' : '')}
        </p>
      </div>

      {isAdmin && isAssistant && message.model_used && (
        <span className="text-[10px] text-neutral-600 mt-0.5 block">{message.model_used}</span>
      )}
    </div>
  );
}
