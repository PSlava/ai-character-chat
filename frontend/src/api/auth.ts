import api from './client';
import { setToken, setUser, removeToken, removeUser } from '@/lib/supabase';

export async function signUp(email: string, password: string, username?: string) {
  const { data } = await api.post('/auth/register', { email, password, ...(username && { username }) });
  setToken(data.token);
  setUser(data.user);
  return data;
}

export async function signIn(email: string, password: string) {
  const { data } = await api.post('/auth/login', { email, password });
  setToken(data.token);
  setUser(data.user);
  return data;
}

export async function signOut() {
  removeToken();
  removeUser();
}
