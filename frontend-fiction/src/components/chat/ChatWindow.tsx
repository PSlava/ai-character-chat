import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Pencil, Send, Loader2, ArrowDown, ArrowRight } from 'lucide-react';
import type { Message } from '@/types';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: Message[];
  characterName?: string;
  characterAvatar?: string | null;
  userName?: string;
  isStreaming: boolean;
  isAdmin?: boolean;
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
  onDeleteMessage?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
  onContinue?: () => void;
  truncated?: boolean;
  onResendLast?: (editedContent?: string) => void;
}

export function ChatWindow({ messages, characterName, characterAvatar, userName, isStreaming, isAdmin, hasMore, loadingMore, onLoadMore, onDeleteMessage, onRegenerate, onContinue, truncated, onResendLast }: Props) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const prevScrollHeightRef = useRef<number>(0);
  const isPrependingRef = useRef(false);
  const prevMsgCountRef = useRef(messages.length);
  const isNearBottomRef = useRef(true);
  const scrollRAFRef = useRef<number>(0);

  // Auto-scroll to bottom on new messages (but not when prepending old ones)
  useEffect(() => {
    if (isPrependingRef.current) {
      // Restore scroll position after prepending old messages
      const container = containerRef.current;
      if (container) {
        const newScrollHeight = container.scrollHeight;
        container.scrollTop = newScrollHeight - prevScrollHeightRef.current;
      }
      isPrependingRef.current = false;
    } else if (isNearBottomRef.current) {
      // Scroll only the chat container (NOT parent main) to avoid header jumping
      cancelAnimationFrame(scrollRAFRef.current);
      scrollRAFRef.current = requestAnimationFrame(() => {
        const container = containerRef.current;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    }
    prevMsgCountRef.current = messages.length;
  }, [messages, isStreaming]);

  // Cleanup rAF on unmount
  useEffect(() => {
    return () => cancelAnimationFrame(scrollRAFRef.current);
  }, []);

  // Detect scroll to top for loading more + show/hide scroll-to-bottom button
  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    // Track if user is near bottom for auto-scroll decisions
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    isNearBottomRef.current = distanceFromBottom < 150;
    setShowScrollBtn(distanceFromBottom > 300);

    if (!hasMore || loadingMore) return;
    if (container.scrollTop < 100 && onLoadMore) {
      prevScrollHeightRef.current = container.scrollHeight;
      isPrependingRef.current = true;
      onLoadMore();
    }
  }, [hasMore, loadingMore, onLoadMore]);

  const visible = messages.filter((m) => m.role !== 'system');
  const lastMsg = visible.length > 1 ? visible[visible.length - 1] : null;
  const lastIsError = !!(lastMsg?.role === 'assistant' && lastMsg?.isError);

  // Show regenerate under last assistant (including errors)
  const lastAssistant = lastMsg?.role === 'assistant' ? lastMsg : null;

  // Show resend/edit when last is user, OR last is error (treat as no reply)
  let lastUserNoReply: Message | null = null;
  if (lastMsg?.role === 'user') {
    lastUserNoReply = lastMsg;
  } else if (lastIsError) {
    // Find the user message before the error
    for (let i = visible.length - 2; i >= 1; i--) {
      if (visible[i].role === 'user') {
        lastUserNoReply = visible[i];
        break;
      }
    }
  }

  const scrollToBottom = () => {
    const container = containerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  };

  return (
    <div ref={containerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto p-2 sm:p-4 relative">
      <div className="max-w-3xl mx-auto space-y-4">
        {loadingMore && (
          <div className="flex justify-center py-2">
            <Loader2 className="w-5 h-5 text-neutral-500 animate-spin" />
          </div>
        )}
        {visible.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              characterName={characterName}
              characterAvatar={characterAvatar}
              userName={userName}
              isFirstMessage={index === 0}
              isAdmin={isAdmin}
              onDelete={onDeleteMessage}
              onRegenerate={onRegenerate}
            />
          ))}

        {!isStreaming && lastAssistant && onRegenerate && (
          <div className="flex justify-start gap-1">
            <button
              onClick={() => onRegenerate(lastAssistant.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-purple-400 hover:bg-neutral-800 rounded-lg transition-colors"
              title={t('chat.regenerateTooltip')}
            >
              <RefreshCw size={13} />
              {t('chat.regenerate')}
            </button>
            {truncated && onContinue && (
              <button
                onClick={onContinue}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-emerald-400 hover:bg-neutral-800 rounded-lg transition-colors"
                title={t('chat.continueTooltip')}
              >
                <ArrowRight size={13} />
                {t('chat.continue')}
              </button>
            )}
          </div>
        )}

        {!isStreaming && lastUserNoReply && onResendLast && (
          <div className="flex justify-end">
            {editing ? (
              <div className="w-full max-w-[85%] sm:max-w-[75%] space-y-2">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white text-sm resize-none focus:outline-none focus:border-purple-500"
                  rows={3}
                  autoFocus
                />
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => setEditing(false)}
                    className="px-3 py-1.5 text-xs text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    onClick={() => {
                      if (editText.trim()) {
                        onResendLast(editText.trim());
                        setEditing(false);
                      }
                    }}
                    disabled={!editText.trim()}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50"
                  >
                    <Send size={13} />
                    {t('common.send')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-1">
                <button
                  onClick={() => onResendLast()}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-purple-400 hover:bg-neutral-800 rounded-lg transition-colors"
                  title={t('chat.retryTooltip')}
                >
                  <RefreshCw size={13} />
                  {t('chat.retry')}
                </button>
                <button
                  onClick={() => {
                    setEditText(lastUserNoReply.content);
                    setEditing(true);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-purple-400 hover:bg-neutral-800 rounded-lg transition-colors"
                  title={t('chat.editTooltip')}
                >
                  <Pencil size={13} />
                  {t('common.edit')}
                </button>
              </div>
            )}
          </div>
        )}

        {isStreaming && (
          <div className="flex gap-2 items-center text-neutral-500 text-sm">
            <div className="animate-pulse flex gap-1">
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce [animation-delay:0.1s]" />
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce [animation-delay:0.2s]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {showScrollBtn && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 sm:right-6 w-10 h-10 bg-neutral-800 hover:bg-neutral-700 border border-neutral-600 rounded-full flex items-center justify-center text-neutral-300 hover:text-white shadow-lg transition-all"
          aria-label="Scroll to bottom"
        >
          <ArrowDown size={18} />
        </button>
      )}
    </div>
  );
}
