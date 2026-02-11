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

  const hasActions = !isFirstMessage && ((isAssistant && onRegenerate) || onDelete);

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
    <div className={`group flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className="shrink-0 mt-1">
        {isUser ? (
          <Avatar name={t('chat.you')} size="sm" />
        ) : (
          <Avatar src={characterAvatar} name={characterName || 'AI'} size="sm" />
        )}
      </div>
      <div className="relative max-w-[85%] sm:max-w-[75%]">
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            message.isError
              ? 'bg-red-900/30 border border-red-800 text-red-300'
              : isUser
                ? 'bg-purple-600 text-white'
                : 'bg-neutral-800 text-neutral-100'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">
            {message.content || (isAssistant ? '...' : '')}
          </p>
        </div>
        {isAdmin && isAssistant && message.model_used && (
          <span className="text-[10px] text-neutral-600 mt-0.5 block">{message.model_used}</span>
        )}

        {/* Action menu */}
        {hasActions && (
          <div
            ref={menuRef}
            className={`absolute top-1 ${isUser ? '-left-8' : '-right-8'}`}
          >
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="p-1.5 text-neutral-600 hover:text-neutral-300 transition-opacity opacity-50 md:opacity-0 md:group-hover:opacity-100"
            >
              <EllipsisVertical size={16} />
            </button>
            {menuOpen && (
              <div
                className={`absolute z-50 top-full mt-1 py-1 bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl min-w-[160px] ${
                  isUser ? 'right-0' : 'left-0'
                }`}
              >
                {isAssistant && onRegenerate && (
                  <button
                    onClick={() => { onRegenerate(message.id); setMenuOpen(false); }}
                    className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-700 hover:text-white transition-colors"
                  >
                    <RefreshCw size={14} />
                    {t('chat.regenerate')}
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => { onDelete(message.id); setMenuOpen(false); }}
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
    </div>
  );
}
