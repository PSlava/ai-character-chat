import api from './client';

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  language: string;
  role: string;
  message_count: number;
  chat_count: number;
  xp_total: number;
  level: number;
}

export async function getProfile() {
  const { data } = await api.get<UserProfile>('/users/me');
  return data;
}

export async function updateProfile(body: { display_name?: string; username?: string; bio?: string; avatar_url?: string; language?: string }) {
  const { data } = await api.put<UserProfile>('/users/me', body);
  return data;
}

export async function deleteAccount(): Promise<void> {
  await api.delete('/users/me');
}

// Favorites
import type { Character } from '@/types';

export async function getFavorites(): Promise<Character[]> {
  const { data } = await api.get<Character[]>('/users/me/favorites');
  return data;
}

export async function addFavorite(characterId: string): Promise<void> {
  await api.post(`/users/me/favorites/${characterId}`);
}

export async function removeFavorite(characterId: string): Promise<void> {
  await api.delete(`/users/me/favorites/${characterId}`);
}
