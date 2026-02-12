import api from './client';
import { getToken } from '@/lib/supabase';
import type { Chat, ChatDetail, Message } from '@/types';

export async function createChat(characterId: string, model?: string, personaId?: string) {
  const { data } = await api.post<ChatDetail>('/chats', {
    character_id: characterId,
    model,
    persona_id: personaId,
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

export async function getAuthToken(): Promise<string | null> {
  return getToken();
}
