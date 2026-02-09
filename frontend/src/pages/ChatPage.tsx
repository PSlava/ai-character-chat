import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Trash2, Settings } from 'lucide-react';
import { getChat, clearChatMessages, deleteChatMessage } from '@/api/chat';
import { getOpenRouterModels } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import { useChat } from '@/hooks/useChat';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ChatInput } from '@/components/chat/ChatInput';
import { GenerationSettingsModal } from '@/components/chat/GenerationSettingsModal';
import type { ChatSettings } from '@/components/chat/GenerationSettingsModal';
import { Avatar } from '@/components/ui/Avatar';
import type { ChatDetail } from '@/types';

const MODEL_ALIASES: Record<string, string> = {
  claude: 'Claude',
  openai: 'GPT-4o',
  gemini: 'Gemini',
  openrouter: 'OpenRouter Auto',
  deepseek: 'DeepSeek',
  qwen: 'Qwen',
};

export function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const [chatDetail, setChatDetail] = useState<ChatDetail | null>(null);
  const [error, setError] = useState('');
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [chatSettings, setChatSettings] = useState<ChatSettings>({});
  const [activeModel, setActiveModel] = useState('');

  const { messages, setMessages, sendMessage, isStreaming, stopStreaming, setGenerationSettings, regenerate } = useChat(
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
        setActiveModel(data.chat.model_used || 'openrouter');
      })
      .catch(() => setError('Чат не найден'));
  }, [chatId, setMessages]);

  const handleApplySettings = (s: ChatSettings) => {
    setChatSettings(s);
    setGenerationSettings(s);
    if (s.model) {
      setActiveModel(s.model);
    }
  };

  const getModelLabel = (m: string) => {
    if (MODEL_ALIASES[m]) return MODEL_ALIASES[m];
    const found = orModels.find((om) => om.id === m);
    return found ? found.name : m;
  };

  const handleClearChat = async () => {
    if (!chatId || isStreaming) return;
    if (!confirm('Очистить историю чата? Приветственное сообщение останется.')) return;
    try {
      await clearChatMessages(chatId);
      setMessages((prev) => {
        const visible = prev.filter((m) => m.role !== 'system');
        return visible.length > 0 ? [visible[0]] : [];
      });
    } catch {
      setError('Не удалось очистить чат');
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    if (!chatId || isStreaming) return;
    try {
      await deleteChatMessage(chatId, messageId);
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
    } catch {
      // Silently fail — message might be the greeting
    }
  };

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
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold">{character?.name}</h2>
          <p className="text-xs text-neutral-500">{getModelLabel(activeModel)}</p>
        </div>
        <button
          onClick={() => setShowSettings(true)}
          className="flex items-center gap-2 px-3 py-1.5 border border-neutral-700 rounded-lg text-sm text-neutral-300 hover:border-neutral-500 hover:text-white transition-colors"
        >
          <span className="hidden sm:inline">Модель и настройки</span>
          <Settings size={16} />
        </button>
        <button
          onClick={handleClearChat}
          disabled={isStreaming}
          className="p-2 text-neutral-500 hover:text-red-400 transition-colors disabled:opacity-50"
          title="Очистить чат"
        >
          <Trash2 size={18} />
        </button>
      </div>

      <ChatWindow
        messages={messages}
        characterName={character?.name}
        characterAvatar={character?.avatar_url}
        isStreaming={isStreaming}
        onDeleteMessage={handleDeleteMessage}
        onRegenerate={!isStreaming ? regenerate : undefined}
      />

      <ChatInput
        onSend={sendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
      />

      {showSettings && (
        <GenerationSettingsModal
          settings={chatSettings}
          currentModel={activeModel}
          orModels={orModels}
          onApply={handleApplySettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
