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
