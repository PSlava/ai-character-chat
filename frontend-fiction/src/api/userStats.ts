import api from './client';

export interface UserStats {
  adventures_started: number;
  messages_sent: number;
  adventures_rated: number;
  average_rating: number | null;
  achievements_unlocked: number;
  campaigns_created: number;
  level: number;
  xp_total: number;
  xp_current_level: number;
  xp_next_level: number;
  member_since: string | null;
}

export async function getUserStats(): Promise<UserStats> {
  const { data } = await api.get<UserStats>('/users/me/stats');
  return data;
}
