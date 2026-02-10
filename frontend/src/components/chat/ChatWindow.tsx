import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Pencil, Send } from 'lucide-react';
import type { Message } from '@/types';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: Message[];
  characterName?: string;
  characterAvatar?: string | null;
  isStreaming: boolean;
  onDeleteMessage?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
  onResendLast?: (editedContent?: string) => void;
}

export function ChatWindow({ messages, characterName, characterAvatar, isStreaming, onDeleteMessage, onRegenerate, onResendLast }: Props) {
  const { t } = useTranslation();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

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

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-3xl mx-auto space-y-4">
        {visible.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              characterName={characterName}
              characterAvatar={characterAvatar}
              isFirstMessage={index === 0}
              onDelete={onDeleteMessage}
              onRegenerate={onRegenerate}
            />
          ))}

        {!isStreaming && lastAssistant && onRegenerate && (
          <div className="flex justify-start pl-11">
            <button
              onClick={() => onRegenerate(lastAssistant.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-purple-400 hover:bg-neutral-800 rounded-lg transition-colors"
              title={t('chat.regenerateTooltip')}
            >
              <RefreshCw size={13} />
              {t('chat.regenerate')}
            </button>
          </div>
        )}

        {!isStreaming && lastUserNoReply && onResendLast && (
          <div className="flex justify-end pr-11">
            {editing ? (
              <div className="w-full max-w-[75%] space-y-2">
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
    </div>
  );
}
