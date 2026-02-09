import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import type { Message } from '@/types';
import { Avatar } from '@/components/ui/Avatar';

interface Props {
  message: Message;
  characterName?: string;
  characterAvatar?: string | null;
  isFirstMessage?: boolean;
  onDelete?: (messageId: string) => void;
}

export function MessageBubble({ message, characterName, characterAvatar, isFirstMessage, onDelete }: Props) {
  const isUser = message.role === 'user';
  const [hovering, setHovering] = useState(false);

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} group`}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <div className="shrink-0 mt-1">
        {isUser ? (
          <Avatar name="Вы" size="sm" />
        ) : (
          <Avatar src={characterAvatar} name={characterName || 'AI'} size="sm" />
        )}
      </div>
      <div className="relative max-w-[75%]">
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isUser
              ? 'bg-purple-600 text-white'
              : 'bg-neutral-800 text-neutral-100'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>
        {!isFirstMessage && onDelete && hovering && (
          <button
            onClick={() => onDelete(message.id)}
            className={`absolute top-1 ${isUser ? '-left-8' : '-right-8'} p-1 text-neutral-500 hover:text-red-400 transition-colors`}
            title="Удалить сообщение"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
