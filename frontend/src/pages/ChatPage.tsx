import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getChat } from '@/api/chat';
import { getOpenRouterModels } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import { useChat } from '@/hooks/useChat';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ChatInput } from '@/components/chat/ChatInput';
import { Avatar } from '@/components/ui/Avatar';
import type { ChatDetail } from '@/types';

export function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const [chatDetail, setChatDetail] = useState<ChatDetail | null>(null);
  const [error, setError] = useState('');
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);

  const { messages, setMessages, sendMessage, isStreaming, stopStreaming } = useChat(
    chatId || ''
  );

  useEffect(() => {
    getOpenRouterModels().then(setOrModels).catch(() => {});
  }, []);

  useEffect(() => {
    if (!chatId) return;
    getChat(chatId)
      .then((data) => {
        setChatDetail(data);
        setMessages(data.messages);
      })
      .catch(() => setError('Чат не найден'));
  }, [chatId, setMessages]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400">
        {error}
      </div>
    );
  }

  if (!chatDetail) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-neutral-500">Загрузка...</div>
      </div>
    );
  }

  const character = chatDetail.chat.characters;

  return (
    <div className="h-full flex flex-col">
      {/* Chat header */}
      <div className="border-b border-neutral-800 px-4 py-3 flex items-center gap-3">
        <Avatar
          src={character?.avatar_url}
          name={character?.name || '?'}
          size="sm"
        />
        <div>
          <h2 className="font-semibold">{character?.name}</h2>
          <p className="text-xs text-neutral-500">
            {(() => {
              const m = chatDetail.chat.model_used || '';
              const alias: Record<string, string> = { claude: 'Claude', openai: 'GPT-4o', gemini: 'Gemini', openrouter: 'OpenRouter Auto' };
              if (alias[m]) return alias[m];
              const found = orModels.find((om) => om.id === m);
              return found ? found.name : m;
            })()}
          </p>
        </div>
      </div>

      <ChatWindow
        messages={messages}
        characterName={character?.name}
        characterAvatar={character?.avatar_url}
        isStreaming={isStreaming}
      />

      <ChatInput
        onSend={sendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
      />
    </div>
  );
}
