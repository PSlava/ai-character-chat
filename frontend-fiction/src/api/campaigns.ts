import api from './client';
import type { Campaign, CampaignDetail, DiceRollResult } from '@/types';

export interface CampaignCreateBody {
  name: string;
  description?: string;
  character_id: string;
  system?: string;
}

export async function createCampaign(body: CampaignCreateBody) {
  const { data } = await api.post<{ id: string; name: string; session: { id: string; chat_id: string; number: number } }>('/campaigns', body);
  return data;
}

export async function getCampaigns() {
  const { data } = await api.get<Campaign[]>('/campaigns');
  return data;
}

export async function getCampaign(campaignId: string) {
  const { data } = await api.get<CampaignDetail>(`/campaigns/${campaignId}`);
  return data;
}

export async function createSession(campaignId: string) {
  const { data } = await api.post<{ id: string; chat_id: string; number: number }>(`/campaigns/${campaignId}/sessions`);
  return data;
}

export async function deleteCampaign(campaignId: string) {
  await api.delete(`/campaigns/${campaignId}`);
}

export async function rollDice(expression: string) {
  const { data } = await api.post<DiceRollResult>('/game/roll', { expression });
  return data;
}
