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
}

export async function getProfile() {
  const { data } = await api.get<UserProfile>('/users/me');
  return data;
}

export async function updateProfile(body: { display_name?: string; username?: string; bio?: string; avatar_url?: string; language?: string }) {
  const { data } = await api.put<UserProfile>('/users/me', body);
  return data;
}
