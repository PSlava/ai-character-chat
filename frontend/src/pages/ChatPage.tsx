import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import { Trash2, RotateCcw, Settings } from 'lucide-react';
import { getChat, deleteChat, clearChatMessages, deleteChatMessage, getOlderMessages } from '@/api/chat';
import { getOpenRouterModels, getGroqModels, getCerebrasModels, getTogetherModels } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import { useChat } from '@/hooks/useChat';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ChatInput } from '@/components/chat/ChatInput';
import { GenerationSettingsModal, loadModelSettings } from '@/components/chat/GenerationSettingsModal';
import type { ChatSettings } from '@/components/chat/GenerationSettingsModal';
import { Avatar } from '@/components/ui/Avatar';
import type { ChatDetail } from '@/types';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';

const MODEL_ALIASES: Record<string, string> = {
  claude: 'Claude',
  openai: 'GPT-4o',
  gemini: 'Gemini',
  openrouter: 'OpenRouter Auto',
  deepseek: 'DeepSeek',
  qwen: 'Qwen',
  groq: 'Groq',
  cerebras: 'Cerebras',
  together: 'Together',
};

export function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const [chatDetail, setChatDetail] = useState<ChatDetail | null>(null);
  const [error, setError] = useState('');
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);
  const [groqModels, setGroqModels] = useState<OpenRouterModel[]>([]);
  const [cerebrasModels, setCerebrasModels] = useState<OpenRouterModel[]>([]);
  const [togetherModels, setTogetherModels] = useState<OpenRouterModel[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [activeModel, setActiveModel] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const authUser = useAuthStore((s) => s.user);
  const removeChat = useChatStore((s) => s.removeChat);
  const isAdmin = authUser?.role === 'admin';

  const { messages, setMessages, sendMessage, isStreaming, stopStreaming, setGenerationSettings, regenerate, resendLast } = useChat(
    chatId || ''
  );

  useEffect(() => {
    getOpenRouterModels().then(setOrModels).catch(() => {});
    getGroqModels().then(setGroqModels).catch(() => {});
    getCerebrasModels().then(setCerebrasModels).catch(() => {});
    getTogetherModels().then(setTogetherModels).catch(() => {});
  }, []);

  useEffect(() => {
    if (!chatId) return;
    getChat(chatId)
      .then((data) => {
        setChatDetail(data);
        setMessages(data.messages);
        setHasMore(data.has_more);

        // Migrate old format: chat-settings:{chatId} → chat-model:{chatId}
        let savedModel: string | null = null;
        try {
          savedModel = localStorage.getItem(`chat-model:${chatId}`);
          if (!savedModel) {
            const old = localStorage.getItem(`chat-settings:${chatId}`);
            if (old) {
              const parsed = JSON.parse(old);
              if (parsed.model) {
                savedModel = parsed.model;
                localStorage.setItem(`chat-model:${chatId}`, savedModel!);
              }
              localStorage.removeItem(`chat-settings:${chatId}`);
            }
          }
        } catch {}

        const model = savedModel || data.chat.model_used || 'openrouter';
        setActiveModel(model);
        setGenerationSettings(loadModelSettings(model));
      })
      .catch(() => setError(t('chat.notFound')));
  }, [chatId, setMessages]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLoadMore = useCallback(async () => {
    if (!chatId || loadingMore || !hasMore) return;
    const firstMsg = messages.find((m) => m.role !== 'system');
    if (!firstMsg) return;
    setLoadingMore(true);
    try {
      const data = await getOlderMessages(chatId, firstMsg.id);
      setMessages((prev) => [...data.messages, ...prev]);
      setHasMore(data.has_more);
    } catch {
      // silently fail
    } finally {
      setLoadingMore(false);
    }
  }, [chatId, loadingMore, hasMore, messages, setMessages]);

  const handleApplySettings = (s: ChatSettings) => {
    setGenerationSettings(s);
    if (s.model) {
      setActiveModel(s.model);
      if (chatId) {
        try { localStorage.setItem(`chat-model:${chatId}`, s.model); } catch {}
      }
    }
  };

  const getModelLabel = (m: string) => {
    if (MODEL_ALIASES[m]) return MODEL_ALIASES[m];
    if (m.startsWith('groq:')) {
      const id = m.slice(5);
      const found = groqModels.find((gm) => gm.id === id);
      return found ? `Groq: ${found.name}` : `Groq: ${id}`;
    }
    if (m.startsWith('cerebras:')) {
      const id = m.slice(9);
      const found = cerebrasModels.find((cm) => cm.id === id);
      return found ? `Cerebras: ${found.name}` : `Cerebras: ${id}`;
    }
    if (m.startsWith('together:')) {
      const id = m.slice(9);
      const found = togetherModels.find((tm) => tm.id === id);
      return found ? `Together: ${found.name}` : `Together: ${id}`;
    }
    const found = orModels.find((om) => om.id === m);
    return found ? found.name : m;
  };

  const handleDeleteChat = async () => {
    if (!chatId || isStreaming) return;
    if (!confirm(t('chat.deleteConfirm'))) return;
    try {
      await deleteChat(chatId);
      removeChat(chatId);
      navigate('/');
    } catch {
      setError(t('chat.deleteError'));
    }
  };

  const handleClearChat = async () => {
    if (!chatId || isStreaming) return;
    if (!confirm(t('chat.clearConfirm'))) return;
    try {
      await clearChatMessages(chatId);
      // Reload chat to get only the greeting message
      const data = await getChat(chatId);
      setMessages(data.messages);
      setHasMore(data.has_more);
    } catch {
      setError(t('chat.clearError'));
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    if (!chatId || isStreaming) return;
    // Check if it's an error message (local only, not in DB)
    const msg = messages.find((m) => m.id === messageId);
    if (msg?.isError) {
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
      return;
    }
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
        <div className="animate-pulse text-neutral-500">{t('common.loading')}</div>
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
          <span className="hidden sm:inline">{t('chat.modelAndSettings')}</span>
          <Settings size={16} />
        </button>
        <button
          onClick={handleClearChat}
          disabled={isStreaming}
          className="p-2 text-neutral-500 hover:text-yellow-400 transition-colors disabled:opacity-50"
          title={t('chat.clearChat')}
        >
          <RotateCcw size={18} />
        </button>
        <button
          onClick={handleDeleteChat}
          disabled={isStreaming}
          className="p-2 text-neutral-500 hover:text-red-400 transition-colors disabled:opacity-50"
          title={t('chat.deleteChat')}
        >
          <Trash2 size={18} />
        </button>
      </div>

      <ChatWindow
        messages={messages}
        characterName={character?.name}
        characterAvatar={character?.avatar_url}
        isStreaming={isStreaming}
        isAdmin={isAdmin}
        hasMore={hasMore}
        loadingMore={loadingMore}
        onLoadMore={handleLoadMore}
        onDeleteMessage={handleDeleteMessage}
        onRegenerate={!isStreaming ? regenerate : undefined}
        onResendLast={!isStreaming ? resendLast : undefined}
      />

      <ChatInput
        onSend={sendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
      />

      {showSettings && (
        <GenerationSettingsModal
          currentModel={activeModel}
          orModels={orModels}
          groqModels={groqModels}
          cerebrasModels={cerebrasModels}
          togetherModels={togetherModels}
          contentRating={character?.content_rating}
          onApply={handleApplySettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
