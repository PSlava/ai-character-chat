import api from './client';

export interface GroupChatMember {
  id: string;
  character_id: string;
  position: number;
  character: {
    id: string;
    name: string;
    avatar_url: string | null;
    tagline: string | null;
  } | null;
}

export interface GroupChat {
  id: string;
  user_id: string;
  title: string | null;
  members: GroupChatMember[];
  created_at: string;
  updated_at: string;
}

export interface GroupMessage {
  id: string;
  group_chat_id: string;
  character_id: string | null;
  role: 'user' | 'assistant';
  content: string;
  model_used: string | null;
  created_at: string;
}

export interface GroupChatDetail {
  chat: GroupChat;
  messages: GroupMessage[];
}

export async function createGroupChat(characterIds: string[], title?: string): Promise<GroupChat> {
  const { data } = await api.post<GroupChat>('/group-chats', {
    character_ids: characterIds,
    title,
  });
  return data;
}

export async function getGroupChats(): Promise<GroupChat[]> {
  const { data } = await api.get<GroupChat[]>('/group-chats');
  return data;
}

export async function getGroupChat(chatId: string): Promise<GroupChatDetail> {
  const { data } = await api.get<GroupChatDetail>(`/group-chats/${chatId}`);
  return data;
}

export async function deleteGroupChat(chatId: string): Promise<void> {
  await api.delete(`/group-chats/${chatId}`);
}
