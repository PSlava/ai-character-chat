import { useEffect, useRef } from 'react';
import type { Message } from '@/types';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: Message[];
  characterName?: string;
  characterAvatar?: string | null;
  isStreaming: boolean;
  onDeleteMessage?: (messageId: string) => void;
}

export function ChatWindow({ messages, characterName, characterAvatar, isStreaming, onDeleteMessage }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const visible = messages.filter((m) => m.role !== 'system');

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
            />
          ))}

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
