import api from './client';

// --- Page view tracking (public, fire-and-forget) ---

export function trackPageView(path: string): void {
  const referrer = document.referrer || undefined;
  api.post('/analytics/pageview', { path, referrer }).catch(() => {});
}

// --- Admin analytics dashboard ---

export interface AnalyticsSummary {
  users_total: number;
  users_new: number;
  pageviews: number;
  unique_visitors: number;
  messages: number;
  new_chats: number;
}

export interface DailyStats {
  date: string;
  pageviews: number;
  unique_visitors: number;
  registrations: number;
  messages: number;
  chats: number;
}

export interface TopPage {
  path: string;
  views: number;
  unique: number;
}

export interface TopReferrer {
  referrer: string;
  views: number;
  unique: number;
}

export interface TopCharacter {
  id: string;
  name: string;
  avatar_url: string | null;
  messages: number;
}

export interface ModelUsage {
  model: string;
  count: number;
}

export interface CountryStats {
  country: string;
  views: number;
  unique: number;
}

export interface AnalyticsOverview {
  summary: AnalyticsSummary;
  daily: DailyStats[];
  top_pages: TopPage[];
  top_referrers: TopReferrer[];
  top_characters: TopCharacter[];
  devices: { mobile: number; desktop: number; tablet: number };
  models: ModelUsage[];
  countries: CountryStats[];
}

export async function getAnalyticsOverview(days: number = 7): Promise<AnalyticsOverview> {
  const { data } = await api.get<AnalyticsOverview>('/admin/analytics/overview', {
    params: { days },
  });
  return data;
}
