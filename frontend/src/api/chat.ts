import api from './client';
import { getToken } from '@/lib/supabase';
import type { Chat, ChatDetail } from '@/types';

export async function createChat(characterId: string, model?: string) {
  const { data } = await api.post<ChatDetail>('/chats', {
    character_id: characterId,
    model,
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

export async function getAuthToken(): Promise<string | null> {
  return getToken();
}
