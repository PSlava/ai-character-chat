import { useState, useCallback, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { getAuthToken } from '@/api/chat';
import type { Message } from '@/types';

export interface GenerationSettings {
  model?: string;
  temperature?: number;
  top_p?: number;
  top_k?: number;
  frequency_penalty?: number;
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
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, id: data.message_id };
              }
              return updated;
            });
            setIsStreaming(false);
          }
          if (data.type === 'error') {
            setIsStreaming(false);
          }
        },
        onerror() {
          setIsStreaming(false);
        },
      });
    },
    [chatId]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { messages, setMessages, sendMessage, isStreaming, stopStreaming, setGenerationSettings };
}
