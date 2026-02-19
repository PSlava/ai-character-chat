import { useState, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { getAuthOrAnonToken, deleteChatMessage } from '@/api/chat';
import type { Message } from '@/types';

export interface GenerationSettings {
  model?: string;
  temperature?: number;
  top_p?: number;
  top_k?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  max_tokens?: number;
  context_limit?: number;
}

export function useChat(chatId: string, initialMessages: Message[] = []) {
  const { t, i18n } = useTranslation();
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [anonLimitReached, setAnonLimitReached] = useState(false);
  const [anonMessagesLeft, setAnonMessagesLeft] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const settingsRef = useRef<GenerationSettings>({});

  const setGenerationSettings = useCallback((s: GenerationSettings) => {
    settingsRef.current = s;
  }, []);

  const sendMessage = useCallback(
    async (content: string, opts?: { is_regenerate?: boolean }) => {
      const { token, anonSessionId } = getAuthOrAnonToken();
      if (!token && !anonSessionId) return;

      // Add user message optimistically
      const userMsg: Message = {
        id: crypto.randomUUID(),
        chat_id: chatId,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);

      // Add empty assistant message for streaming
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        chat_id: chatId,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      } else if (anonSessionId) {
        headers['X-Anon-Session'] = anonSessionId;
      }

      const s = settingsRef.current;
      await fetchEventSource(`/api/chats/${chatId}/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          content,
          language: i18n.language,
          ...(opts?.is_regenerate && { is_regenerate: true }),
          ...(s.model && { model: s.model }),
          ...(s.temperature !== undefined && { temperature: s.temperature }),
          ...(s.top_p !== undefined && { top_p: s.top_p }),
          ...(s.top_k !== undefined && { top_k: s.top_k }),
          ...(s.frequency_penalty !== undefined && { frequency_penalty: s.frequency_penalty }),
          ...(s.presence_penalty !== undefined && { presence_penalty: s.presence_penalty }),
          ...(s.max_tokens !== undefined && { max_tokens: s.max_tokens }),
          ...(s.context_limit && { context_limit: s.context_limit }),
        }),
        signal: ctrl.signal,
        onmessage(event) {
          let data: any;
          try { data = JSON.parse(event.data); } catch { return; }
          if (data.type === 'token') {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  content: last.content + data.content,
                };
              }
              return updated;
            });
          }
          if (data.type === 'done') {
            setMessages((prev) => {
              const updated = [...prev];
              // Update assistant message with real DB id
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, id: data.message_id, model_used: data.model_used };
              }
              // Update user message with real DB id
              if (data.user_message_id) {
                for (let i = updated.length - 2; i >= 0; i--) {
                  if (updated[i].role === 'user' && updated[i].id === userMsg.id) {
                    updated[i] = { ...updated[i], id: data.user_message_id };
                    break;
                  }
                }
              }
              return updated;
            });
            // Track anonymous messages remaining
            if (data.anon_messages_left !== undefined) {
              setAnonMessagesLeft(data.anon_messages_left);
              if (data.anon_messages_left <= 0) {
                setAnonLimitReached(true);
              }
            }
            setIsStreaming(false);
          }
          if (data.type === 'error') {
            // Show error in the assistant message bubble
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  content: data.content || t('chat.generationError'),
                  isError: true,
                };
              }
              // Sync user message ID even on error (so regenerate can delete it)
              if (data.user_message_id) {
                for (let i = updated.length - 2; i >= 0; i--) {
                  if (updated[i].role === 'user' && updated[i].id === userMsg.id) {
                    updated[i] = { ...updated[i], id: data.user_message_id };
                    break;
                  }
                }
              }
              return updated;
            });
            setIsStreaming(false);
          }
        },
        async onopen(response) {
          if (response.ok) return;
          let detail = '';
          try { const body = await response.json(); detail = body.detail || ''; } catch {}
          if (response.status === 403) {
            if (detail === 'anon_limit_reached' || detail === 'anon_chat_disabled') {
              setAnonLimitReached(true);
              // Remove optimistic messages
              setMessages((prev) => prev.filter((m) => m.id !== userMsg.id && m.id !== assistantMsg.id));
              setIsStreaming(false);
              throw new Error(detail);
            }
          }
          throw new Error(detail || `HTTP ${response.status}`);
        },
        onerror(err) {
          if (err?.message === 'anon_limit_reached' || err?.message === 'anon_chat_disabled') {
            throw err; // Don't retry
          }
          const errText = err?.message && err.message !== 'Failed to fetch'
            ? err.message
            : t('chat.connectionError');
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === 'assistant' && !last.content) {
              updated[updated.length - 1] = {
                ...last,
                content: errText,
                isError: true,
              };
            }
            return updated;
          });
          setIsStreaming(false);
          throw err; // Don't retry
        },
      });
    },
    [chatId]
  );

  const regenerate = useCallback(
    async (messageId: string) => {
      // Extract info from current messages synchronously
      let userContent: string | null = null;
      let userMsgId: string | null = null;

      setMessages((prev) => {
        const idx = prev.findIndex((m) => m.id === messageId);
        if (idx === -1) return prev;

        const assistantMsg = prev[idx];
        if (assistantMsg.role !== 'assistant') return prev;

        // Find the user message right before it
        let userIdx = idx - 1;
        while (userIdx >= 0 && prev[userIdx].role !== 'user') userIdx--;
        if (userIdx < 0) return prev;

        userContent = prev[userIdx].content;
        userMsgId = prev[userIdx].id;

        // Remove only the assistant message; keep user message visible
        return prev.filter((_, i) => i !== idx);
      });

      if (!userContent || !userMsgId) return;

      // Delete both from DB, then resend (sendMessage will replace the user message)
      await deleteChatMessage(chatId, messageId).catch(() => {});
      await deleteChatMessage(chatId, userMsgId).catch(() => {});

      // Remove the old user message right before resending so sendMessage adds a fresh one
      setMessages((prev) => prev.filter((m) => m.id !== userMsgId));
      sendMessage(userContent, { is_regenerate: true });
    },
    [chatId, sendMessage]
  );

  const resendLast = useCallback(
    async (editedContent?: string) => {
      setMessages((prev) => {
        const visible = prev.filter((m) => m.role !== 'system');
        const last = visible[visible.length - 1];
        if (!last) return prev;

        // If last is error assistant — find user message before it
        let userMsg: Message | null = null;
        let errorMsg: Message | null = null;

        if (last.role === 'user') {
          userMsg = last;
        } else if (last.role === 'assistant' && last.isError) {
          errorMsg = last;
          // Find the user message before the error
          for (let i = visible.length - 2; i >= 0; i--) {
            if (visible[i].role === 'user') {
              userMsg = visible[i];
              break;
            }
          }
        }

        if (!userMsg) return prev;

        const content = editedContent ?? userMsg.content;
        const idsToRemove = new Set([userMsg.id]);
        if (errorMsg) idsToRemove.add(errorMsg.id);

        const updated = prev.filter((m) => !idsToRemove.has(m.id));

        // Delete user message from DB (error message is local-only), then resend
        (async () => {
          await deleteChatMessage(chatId, userMsg!.id).catch(() => {});
          sendMessage(content);
        })();

        return updated;
      });
    },
    [chatId, sendMessage]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { messages, setMessages, sendMessage, isStreaming, stopStreaming, setGenerationSettings, regenerate, resendLast, anonLimitReached, anonMessagesLeft, setAnonMessagesLeft };
}
