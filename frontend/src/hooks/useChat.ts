import { useState, useCallback, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { getAuthToken, deleteChatMessage } from '@/api/chat';
import type { Message } from '@/types';

export interface GenerationSettings {
  model?: string;
  temperature?: number;
  top_p?: number;
  top_k?: number;
  frequency_penalty?: number;
  max_tokens?: number;
}

export function useChat(chatId: string, initialMessages: Message[] = []) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const settingsRef = useRef<GenerationSettings>({});

  const setGenerationSettings = useCallback((s: GenerationSettings) => {
    settingsRef.current = s;
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      const token = await getAuthToken();
      if (!token) return;

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

      const s = settingsRef.current;
      await fetchEventSource(`/api/chats/${chatId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content,
          ...(s.model && { model: s.model }),
          ...(s.temperature !== undefined && { temperature: s.temperature }),
          ...(s.top_p !== undefined && { top_p: s.top_p }),
          ...(s.top_k !== undefined && { top_k: s.top_k }),
          ...(s.frequency_penalty !== undefined && { frequency_penalty: s.frequency_penalty }),
          ...(s.max_tokens !== undefined && { max_tokens: s.max_tokens }),
        }),
        signal: ctrl.signal,
        onmessage(event) {
          const data = JSON.parse(event.data);
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
                updated[updated.length - 1] = { ...last, id: data.message_id };
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
                  content: data.content || 'Ошибка генерации',
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
        onerror() {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === 'assistant' && !last.content) {
              updated[updated.length - 1] = {
                ...last,
                content: 'Ошибка соединения с сервером',
                isError: true,
              };
            }
            return updated;
          });
          setIsStreaming(false);
        },
      });
    },
    [chatId]
  );

  const regenerate = useCallback(
    async (messageId: string) => {
      // Find the assistant message and the user message before it
      setMessages((prev) => {
        const idx = prev.findIndex((m) => m.id === messageId);
        if (idx === -1) return prev;

        const assistantMsg = prev[idx];
        if (assistantMsg.role !== 'assistant') return prev;

        // Find the user message right before it
        let userIdx = idx - 1;
        while (userIdx >= 0 && prev[userIdx].role !== 'user') userIdx--;
        if (userIdx < 0) return prev;

        const userContent = prev[userIdx].content;
        const userMsgId = prev[userIdx].id;

        // Remove both messages from state
        const updated = prev.filter((_, i) => i !== idx && i !== userIdx);

        // Delete from DB in background, then resend
        (async () => {
          try {
            // Delete saved messages from DB (ignore errors for optimistic messages)
            await deleteChatMessage(chatId, messageId).catch(() => {});
            await deleteChatMessage(chatId, userMsgId).catch(() => {});
          } finally {
            // Resend the user message
            sendMessage(userContent);
          }
        })();

        return updated;
      });
    },
    [chatId, sendMessage]
  );

  const resendLast = useCallback(
    async (editedContent?: string) => {
      // Find the last user message (no assistant reply after it)
      setMessages((prev) => {
        const visible = prev.filter((m) => m.role !== 'system');
        const last = visible[visible.length - 1];
        if (!last || last.role !== 'user') return prev;

        const content = editedContent ?? last.content;
        const msgId = last.id;

        // Remove from state
        const updated = prev.filter((m) => m.id !== msgId);

        // Delete from DB then resend
        (async () => {
          await deleteChatMessage(chatId, msgId).catch(() => {});
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

  return { messages, setMessages, sendMessage, isStreaming, stopStreaming, setGenerationSettings, regenerate, resendLast };
}
