import api from './client';
import type { Character } from '@/types';

export async function getCharacters(params?: {
  search?: string;
  tag?: string;
  limit?: number;
  offset?: number;
}) {
  const { data } = await api.get<Character[]>('/characters', { params });
  return data;
}

export async function getCharacter(id: string) {
  const { data } = await api.get<Character>(`/characters/${id}`);
  return data;
}

export async function getMyCharacters() {
  const { data } = await api.get<Character[]>('/characters/my');
  return data;
}

export async function createCharacter(body: Partial<Character>) {
  const { data } = await api.post<Character>('/characters', body);
  return data;
}

export async function updateCharacter(id: string, body: Partial<Character>) {
  const { data } = await api.put<Character>(`/characters/${id}`, body);
  return data;
}

export async function deleteCharacter(id: string) {
  await api.delete(`/characters/${id}`);
}
