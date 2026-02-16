import api from './client';
import { getToken, getAnonSessionId } from '@/lib/supabase';
import type { Chat, ChatDetail, Message } from '@/types';

export interface AnonLimit {
  limit: number;
  remaining: number;
  enabled: boolean;
}

export async function createChat(characterId: string, model?: string, personaId?: string, forceNew?: boolean) {
  const { data } = await api.post<ChatDetail>('/chats', {
    character_id: characterId,
    model,
    persona_id: personaId,
    force_new: forceNew || false,
  });
  return data;
}

export async function getChats() {
  const { data } = await api.get<Chat[]>('/chats');
  return data;
}

export async function getChat(chatId: string) {
  const { data } = await api.get<ChatDetail>(`/chats/${chatId}`);
  return data;
}

export async function deleteChat(chatId: string) {
  await api.delete(`/chats/${chatId}`);
}

export async function clearChatMessages(chatId: string) {
  await api.delete(`/chats/${chatId}/messages`);
}

export async function deleteChatMessage(chatId: string, messageId: string) {
  await api.delete(`/chats/${chatId}/messages/${messageId}`);
}

export async function getOlderMessages(chatId: string, beforeId: string, limit = 20) {
  const { data } = await api.get<{ messages: Message[]; has_more: boolean }>(
    `/chats/${chatId}/messages`,
    { params: { before: beforeId, limit } },
  );
  return data;
}

export async function getDailyUsage(): Promise<{ used: number; limit: number }> {
  const { data } = await api.get<{ used: number; limit: number }>('/chats/daily-usage');
  return data;
}

export async function generatePersonaReply(chatId: string): Promise<{ content: string }> {
  const { data } = await api.post<{ content: string }>(`/chats/${chatId}/generate-persona-reply`);
  return data;
}

export async function getAuthToken(): Promise<string | null> {
  return getToken();
}

/** Returns token or anon session ID for SSE requests */
export function getAuthOrAnonToken(): { token: string | null; anonSessionId: string | null } {
  const token = getToken();
  if (token) return { token, anonSessionId: null };
  return { token: null, anonSessionId: getAnonSessionId() };
}

export async function getAnonLimit(): Promise<AnonLimit> {
  const { data } = await api.get<AnonLimit>('/chats/anon-limit');
  return data;
}
