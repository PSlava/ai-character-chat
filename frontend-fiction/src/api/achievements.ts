import api from './client';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  target?: number;
  progress?: number;
  unlocked: boolean;
  achieved_at: string | null;
}

export async function getAchievements(language: string): Promise<Achievement[]> {
  const { data } = await api.get<Achievement[]>('/achievements', { params: { language } });
  return data;
}
