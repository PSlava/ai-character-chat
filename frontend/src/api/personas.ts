import api from './client';
import type { Persona } from '@/types';

export async function getPersonas() {
  const { data } = await api.get<Persona[]>('/personas');
  return data;
}

export async function createPersona(body: { name: string; description?: string; is_default?: boolean }) {
  const { data } = await api.post<Persona>('/personas', body);
  return data;
}

export async function updatePersona(id: string, body: { name?: string; description?: string; is_default?: boolean }) {
  const { data } = await api.put<Persona>(`/personas/${id}`, body);
  return data;
}

export async function deletePersona(id: string) {
  await api.delete(`/personas/${id}`);
}
