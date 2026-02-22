import api from './client';

export interface SiteStats {
  users: number;
  messages: number;
  characters: number;
  online_now: number;
  stories?: number;
}

export async function getStats(): Promise<SiteStats> {
  const { data } = await api.get<SiteStats>('/stats');
  return data;
}
