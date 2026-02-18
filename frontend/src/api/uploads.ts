import api from './client';

export async function uploadAvatar(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<{ url: string }>('/upload/avatar', formData);
  return data.url;
}

export async function generateAvatar(prompt: string): Promise<string> {
  const { data } = await api.post<{ url: string }>('/upload/generate-avatar', { prompt }, { timeout: 130_000 });
  return data.url;
}
