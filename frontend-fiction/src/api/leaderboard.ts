import api from './client';

export interface LeaderboardEntry {
  rank: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  level: number;
  xp_total: number;
  message_count: number;
  chat_count: number;
}

export type LeaderboardSort = 'level' | 'messages' | 'adventures';

export async function getLeaderboard(sort: LeaderboardSort = 'level', limit = 20): Promise<LeaderboardEntry[]> {
  const { data } = await api.get<LeaderboardEntry[]>('/users/leaderboard', { params: { sort, limit } });
  return data;
}
