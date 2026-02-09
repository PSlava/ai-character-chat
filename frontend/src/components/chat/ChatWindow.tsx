import { useState, useEffect, useRef } from 'react';
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
  const bottomRef = useRef<HTMLDivElement>(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const visible = messages.filter((m) => m.role !== 'system');
  const lastAssistant = visible.length > 1 && visible[visible.length - 1].role === 'assistant'
    ? visible[visible.length - 1]
    : null;
  const lastUserNoReply = visible.length > 1 && visible[visible.length - 1].role === 'user'
    ? visible[visible.length - 1]
    : null;

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
              title="Перегенерировать ответ"
            >
              <RefreshCw size={13} />
              Перегенерировать
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
                    Отмена
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
                    Отправить
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-1">
                <button
                  onClick={() => onResendLast()}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-purple-400 hover:bg-neutral-800 rounded-lg transition-colors"
                  title="Повторить отправку"
                >
                  <RefreshCw size={13} />
                  Повторить
                </button>
                <button
                  onClick={() => {
                    setEditText(lastUserNoReply.content);
                    setEditing(true);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-500 hover:text-purple-400 hover:bg-neutral-800 rounded-lg transition-colors"
                  title="Редактировать и отправить"
                >
                  <Pencil size={13} />
                  Редактировать
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
