import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import { Trash2, RefreshCw, EllipsisVertical, Copy } from 'lucide-react';
import type { Message } from '@/types';
import { Avatar } from '@/components/ui/Avatar';

interface Props {
  message: Message;
  characterName?: string;
  characterAvatar?: string | null;
  userName?: string;
  isFirstMessage?: boolean;
  isAdmin?: boolean;
  onDelete?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
}

export function MessageBubble({ message, characterName, characterAvatar, userName, isFirstMessage, isAdmin, onDelete, onRegenerate }: Props) {
  const { t } = useTranslation();
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const displayName = isUser ? (userName || t('chat.you')) : characterName;
  const canRegenerate = isAssistant && !isFirstMessage && !!onRegenerate;
  const canDelete = !isFirstMessage && !!onDelete;

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
      <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : ''}`}>
        {isUser ? (
          <Avatar name={displayName || t('chat.you')} size="sm" />
        ) : (
          <Avatar src={characterAvatar} name={characterName || 'AI'} size="sm" />
        )}
        <span className="text-sm font-medium text-neutral-300">
          {displayName}
        </span>

        {/* Action buttons — right next to name */}
        {!isFirstMessage && (canRegenerate || canDelete) && (
          <div className="flex items-center gap-0.5">
            {canRegenerate && (
              <button
                onClick={() => onRegenerate!(message.id)}
                className="flex items-center gap-1.5 px-2 py-1 text-neutral-500 hover:text-neutral-300 rounded-md transition-colors"
              >
                <RefreshCw size={14} />
                <span className="hidden sm:inline text-xs">{t('chat.regenerate')}</span>
              </button>
            )}
            {canDelete && (
              <div ref={menuRef} className="relative">
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="p-1.5 text-neutral-500 hover:text-neutral-300 rounded-md transition-colors"
                >
                  <EllipsisVertical size={18} />
                </button>
                {menuOpen && (
                  <div
                    className={`absolute z-50 top-full mt-1 py-1 bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl min-w-[160px] ${
                      isUser ? 'left-0' : 'right-0'
                    }`}
                  >
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(message.content);
                        toast.success(t('toast.copied'));
                        setMenuOpen(false);
                      }}
                      className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-700 hover:text-white transition-colors"
                    >
                      <Copy size={14} />
                      {t('chat.copyMessage')}
                    </button>
                    <button
                      onClick={() => { onDelete!(message.id); setMenuOpen(false); }}
                      className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-700 hover:text-red-400 transition-colors"
                    >
                      <Trash2 size={14} />
                      {t('chat.deleteMessage')}
                    </button>
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
                  : 'bg-rose-600 text-white'
              }`
            : `${
                message.isError
                  ? 'bg-red-900/30 border border-red-800 text-red-300'
                  : 'bg-neutral-800 text-neutral-100'
              }`
        }`}
      >
{isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <ReactMarkdown
            rehypePlugins={[rehypeSanitize]}
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic text-neutral-300">{children}</em>,
              code: ({ children, className }) => className ? (
                <code className={`${className} text-sm`}>{children}</code>
              ) : (
                <code className="bg-neutral-700 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
              ),
              pre: ({ children }) => <pre className="bg-neutral-700 rounded-lg p-3 my-2 overflow-x-auto text-sm font-mono">{children}</pre>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
              li: ({ children }) => <li className="mb-0.5">{children}</li>,
              blockquote: ({ children }) => <blockquote className="border-l-2 border-rose-500 pl-3 my-2 text-neutral-300 italic">{children}</blockquote>,
            }}
          >
            {message.content || '...'}
          </ReactMarkdown>
        )}
      </div>

      {isAdmin && isAssistant && message.model_used && (
        <span className="text-[10px] text-neutral-600 mt-0.5 block">{message.model_used}</span>
      )}
    </div>
  );
}
