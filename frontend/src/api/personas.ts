import api from './client';
import type { Persona } from '@/types';

export async function getPersonas() {
  const { data } = await api.get<Persona[]>('/personas');
  return data;
}

export async function checkPersonaSlug(slug: string): Promise<{ available: boolean; slug: string; error?: string }> {
  const { data } = await api.get('/personas/check-slug', { params: { slug } });
  return data;
}

export async function createPersona(body: { name: string; slug?: string; description?: string; is_default?: boolean }) {
  const { data } = await api.post<Persona>('/personas', body);
  return data;
}

export async function updatePersona(id: string, body: { name?: string; slug?: string; description?: string; is_default?: boolean }) {
  const { data } = await api.put<Persona>(`/personas/${id}`, body);
  return data;
}

export async function deletePersona(id: string) {
  await api.delete(`/personas/${id}`);
}

export async function getPersonaLimit(): Promise<{ used: number; limit: number }> {
  const { data } = await api.get<{ used: number; limit: number }>('/personas/limit');
  return data;
}
