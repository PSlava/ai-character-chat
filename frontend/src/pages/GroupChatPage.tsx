import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate, Navigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Trash2, Send } from 'lucide-react';
import { getGroupChat, deleteGroupChat } from '@/api/groupChat';
import type { GroupChatDetail, GroupMessage, GroupChatMember } from '@/api/groupChat';
import { useGroupChatStore } from '@/store/groupChatStore';
import { getAuthToken } from '@/api/chat';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Avatar } from '@/components/ui/Avatar';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { SEO } from '@/components/seo/SEO';
import { useAuth } from '@/hooks/useAuth';
import Markdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';

export function GroupChatPage() {
  const { t, i18n } = useTranslation();
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { removeGroupChat } = useGroupChatStore();

  const [detail, setDetail] = useState<GroupChatDetail | null>(null);
  const [messages, setMessages] = useState<GroupMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeCharId, setActiveCharId] = useState<string | null>(null);
  const [showDelete, setShowDelete] = useState(false);
  const [error, setError] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!chatId || !isAuthenticated) return;
    getGroupChat(chatId)
      .then((d) => {
        setDetail(d);
        setMessages(d.messages);
      })
      .catch(() => setError(t('chat.notFound')));
  }, [chatId, isAuthenticated]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const membersMap = detail?.chat.members.reduce<Record<string, GroupChatMember>>((acc, m) => {
    acc[m.character_id] = m;
    return acc;
  }, {}) || {};

  const sendMessage = useCallback(async () => {
    if (!input.trim() || !chatId || isStreaming) return;
    const content = input.trim();
    setInput('');
    setIsStreaming(true);

    const token = await getAuthToken();
    if (!token) return;

    // Optimistic user message
    const tempUserMsg: GroupMessage = {
      id: crypto.randomUUID(),
      group_chat_id: chatId,
      character_id: null,
      role: 'user',
      content,
      model_used: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // Track streaming assistant message per character
    let currentCharMsg: GroupMessage | null = null;

    await fetchEventSource(`/api/group-chats/${chatId}/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content, language: i18n.language }),
      signal: ctrl.signal,
      onmessage(event) {
        let data: any;
        try { data = JSON.parse(event.data); } catch { return; }

        if (data.type === 'user_saved') {
          setMessages((prev) => prev.map((m) =>
            m.id === tempUserMsg.id ? { ...m, id: data.message_id } : m
          ));
        }

        if (data.type === 'character_start') {
          setActiveCharId(data.character_id);
          currentCharMsg = {
            id: crypto.randomUUID(),
            group_chat_id: chatId,
            character_id: data.character_id,
            role: 'assistant',
            content: '',
            model_used: null,
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, currentCharMsg!]);
        }

        if (data.type === 'token' && currentCharMsg) {
          const charId = data.character_id;
          setMessages((prev) => {
            const updated = [...prev];
            for (let i = updated.length - 1; i >= 0; i--) {
              if (updated[i].character_id === charId && updated[i].role === 'assistant') {
                updated[i] = { ...updated[i], content: updated[i].content + data.content };
                break;
              }
            }
            return updated;
          });
        }

        if (data.type === 'character_done') {
          setMessages((prev) => prev.map((m) =>
            m.character_id === data.character_id && m.role === 'assistant' && !m.model_used
              ? { ...m, id: data.message_id, model_used: data.model_used }
              : m
          ));
          setActiveCharId(null);
          currentCharMsg = null;
        }

        if (data.type === 'character_error') {
          setMessages((prev) => prev.map((m) =>
            m.character_id === data.character_id && m.role === 'assistant' && !m.model_used
              ? { ...m, content: data.content || t('chat.generationError') }
              : m
          ));
          setActiveCharId(null);
          currentCharMsg = null;
        }

        if (data.type === 'all_done') {
          setIsStreaming(false);
        }
      },
      onerror() {
        setIsStreaming(false);
      },
    });
  }, [input, chatId, isStreaming, i18n.language]);

  const handleDelete = async () => {
    if (!chatId) return;
    setShowDelete(false);
    try {
      await deleteGroupChat(chatId);
      removeGroupChat(chatId);
      toast.success(t('toast.chatDeleted'));
      navigate('/');
    } catch {
      toast.error(t('chat.deleteError'));
    }
  };

  if (!authLoading && !isAuthenticated) return <Navigate to="/" replace />;
  if (error) return <div className="flex items-center justify-center h-full text-red-400">{error}</div>;
  if (!detail) return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-neutral-500">{t('common.loading')}</div></div>;

  return (
    <div className="flex flex-col h-full">
      <SEO title={detail.chat.title || t('groupChat.title')} />

      {/* Header */}
      <div className="border-b border-neutral-800 px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-2 sm:gap-3">
        <div className="flex -space-x-2">
          {detail.chat.members.slice(0, 4).map((m) => (
            <Avatar
              key={m.id}
              src={m.character?.avatar_url || null}
              name={m.character?.name || '?'}
              size="sm"
            />
          ))}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold truncate">{detail.chat.title}</h2>
          <p className="text-xs text-neutral-500">
            {detail.chat.members.length} {t('groupChat.characters')}
          </p>
        </div>
        <button
          onClick={() => setShowDelete(true)}
          className="p-2 rounded-lg hover:bg-red-900/30 text-neutral-400 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          const member = msg.character_id ? membersMap[msg.character_id] : null;

          return (
            <div key={msg.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <Avatar
                  src={member?.character?.avatar_url || null}
                  name={member?.character?.name || '?'}
                  size="sm"
                />
              )}
              <div className={`max-w-[75%] ${isUser ? 'bg-rose-900/30 border-rose-800/50' : 'bg-neutral-800/50 border-neutral-700/50'} border rounded-xl px-4 py-3`}>
                {!isUser && member?.character && (
                  <p className="text-xs font-medium text-rose-400 mb-1">{member.character.name}</p>
                )}
                {isUser ? (
                  <p className="text-neutral-200 whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-invert prose-sm max-w-none">
                    <Markdown rehypePlugins={[rehypeSanitize]}>{msg.content}</Markdown>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {activeCharId && (
          <div className="flex items-center gap-2 text-neutral-500 text-sm">
            <div className="animate-pulse">
              {membersMap[activeCharId]?.character?.name} {t('groupChat.isTyping')}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-neutral-800 px-3 sm:px-4 py-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder={t('chat.placeholder')}
            disabled={isStreaming}
            className="flex-1 px-4 py-2.5 bg-neutral-800 border border-neutral-700 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-rose-500 disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 rounded-xl text-white transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {showDelete && (
        <ConfirmDialog
          title={t('groupChat.deleteTitle')}
          message={t('groupChat.deleteConfirm')}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}
