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

// User management
export interface AdminUser {
  id: string;
  email: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  role: string;
  is_banned: boolean;
  message_count: number;
  chat_count: number;
  character_count: number;
  language: string;
  created_at: string;
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>('/admin/users');
  return data;
}

export async function banUser(userId: string): Promise<void> {
  await api.put(`/admin/users/${userId}/ban`);
}

export async function unbanUser(userId: string): Promise<void> {
  await api.put(`/admin/users/${userId}/unban`);
}

export async function deleteUser(userId: string): Promise<void> {
  await api.delete(`/admin/users/${userId}`);
}

// Admin settings
export interface AdminSettings {
  notify_registration: string;
  notify_errors: string;
  paid_mode: string;
  cost_mode: string;
  daily_message_limit: string;
  max_personas: string;
  anon_message_limit: string;
}

export async function getAdminSettings(): Promise<AdminSettings> {
  const { data } = await api.get<AdminSettings>('/admin/settings');
  return data;
}

export async function updateAdminSetting(key: string, value: string): Promise<void> {
  await api.put(`/admin/settings/${key}`, { value });
}
