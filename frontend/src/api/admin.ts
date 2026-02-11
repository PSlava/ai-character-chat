import api from './client';

export interface PromptEntry {
  key: string;
  default: string;
  override: string | null;
  updated_at: string | null;
}

export async function getPrompts(): Promise<PromptEntry[]> {
  const { data } = await api.get<PromptEntry[]>('/admin/prompts');
  return data;
}

export async function updatePrompt(key: string, value: string): Promise<void> {
  await api.put(`/admin/prompts/${key}`, { value });
}

export async function resetPrompt(key: string): Promise<void> {
  await api.delete(`/admin/prompts/${key}`);
}

export async function importSeedCharacters(): Promise<{ imported: number }> {
  const { data } = await api.post<{ imported: number }>('/admin/seed-characters');
  return data;
}

export async function deleteSeedCharacters(): Promise<{ deleted: number }> {
  const { data } = await api.delete<{ deleted: number }>('/admin/seed-characters');
  return data;
}

export async function cleanupOrphanAvatars(): Promise<{ deleted: number; kept: number }> {
  const { data } = await api.post<{ deleted: number; kept: number }>('/admin/cleanup-avatars');
  return data;
}
