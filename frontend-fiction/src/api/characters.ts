import api from './client';
import type { Character } from '@/types';

export interface OpenRouterModel {
  id: string;
  name: string;
  quality: number;
  nsfw?: boolean;
  note: string;
}

export interface PaginatedCharacters {
  items: Character[];
  total: number;
}

export async function getCharacters(params?: {
  search?: string;
  tag?: string;
  exclude_tag?: string;
  gender?: string;
  limit?: number;
  offset?: number;
  language?: string;
}) {
  const { data } = await api.get<PaginatedCharacters>('/characters', { params });
  return data;
}

export interface CharacterSuggestion {
  id: string;
  name: string;
  slug: string | null;
  avatar_url: string | null;
  tagline: string;
}

export async function suggestCharacters(q: string, language?: string): Promise<CharacterSuggestion[]> {
  const { data } = await api.get<CharacterSuggestion[]>('/characters/suggest', {
    params: { q, ...(language ? { language } : {}) },
  });
  return data;
}

export async function getCharacter(id: string, language?: string) {
  const { data } = await api.get<Character>(`/characters/${id}`, {
    params: language ? { language } : undefined,
  });
  return data;
}

export async function getCharacterBySlug(slug: string, language?: string) {
  const { data } = await api.get<Character>(`/characters/by-slug/${slug}`, {
    params: language ? { language } : undefined,
  });
  return data;
}

export async function getSimilarCharacters(characterId: string, language?: string): Promise<Character[]> {
  const { data } = await api.get<Character[]>(`/characters/${characterId}/similar`, {
    params: language ? { language } : undefined,
  });
  return data;
}

export async function getMyCharacters() {
  const { data } = await api.get<Character[]>('/characters/my');
  return data;
}

export async function createCharacter(body: Partial<Character>) {
  const { data } = await api.post<Character>('/characters', body);
  return data;
}

export async function updateCharacter(id: string, body: Partial<Character>) {
  const { data } = await api.put<Character>(`/characters/${id}`, body);
  return data;
}

export async function deleteCharacter(id: string) {
  await api.delete(`/characters/${id}`);
}

export interface StructuredTagsResponse {
  categories: { id: string; label_ru: string; label_en: string }[];
  tags: Record<string, { id: string; category: string; label_ru: string; label_en: string }[]>;
}

export async function getStructuredTags(): Promise<StructuredTagsResponse> {
  const { data } = await api.get<StructuredTagsResponse>('/characters/structured-tags');
  return data;
}

export async function getOpenRouterModels(): Promise<OpenRouterModel[]> {
  const { data } = await api.get<OpenRouterModel[]>('/models/openrouter');
  return data;
}

export async function getGroqModels(): Promise<OpenRouterModel[]> {
  const { data } = await api.get<OpenRouterModel[]>('/models/groq');
  return data;
}

export async function getCerebrasModels(): Promise<OpenRouterModel[]> {
  const { data } = await api.get<OpenRouterModel[]>('/models/cerebras');
  return data;
}

export async function getTogetherModels(): Promise<OpenRouterModel[]> {
  const { data } = await api.get<OpenRouterModel[]>('/models/together');
  return data;
}

export async function voteCharacter(characterId: string, value: number): Promise<{ vote_score: number; user_vote: number }> {
  const { data } = await api.post(`/characters/${characterId}/vote`, { value });
  return data;
}

export async function getUserVotes(): Promise<Record<string, number>> {
  const { data } = await api.get<Record<string, number>>('/users/me/votes');
  return data;
}

export async function forkCharacter(characterId: string): Promise<{ id: string; slug: string; name: string }> {
  const { data } = await api.post(`/characters/${characterId}/fork`);
  return data;
}

export interface CharacterRelation {
  relation_type: string;
  label: string;
  character: Character;
}

export async function getCharacterRelations(characterId: string, language?: string): Promise<CharacterRelation[]> {
  const { data } = await api.get<CharacterRelation[]>(`/characters/${characterId}/relations`, {
    params: language ? { language } : undefined,
  });
  return data;
}

/** Wake up Render backend if sleeping. Retries every 3s for up to 3 minutes. */
export async function wakeUpServer(
  onStatus?: (status: string) => void,
): Promise<void> {
  const maxAttempts = 60; // 3 min / 3s
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await api.get('/health', { timeout: 5000 });
      return;
    } catch {
      onStatus?.(`Waiting for server... (${i * 3}s)`);
      await new Promise((r) => setTimeout(r, 3000));
    }
  }
  throw new Error('Server is not responding');
}

export async function generateFromStory(
  storyText: string,
  characterName?: string,
  preferredModel: string = 'auto',
  contentRating: string = 'sfw',
  extraInstructions?: string,
) {
  await wakeUpServer();

  // Call Render backend directly to avoid Vercel proxy timeout (~60s).
  // In dev, falls back to normal api client (proxied by Vite).
  const backendUrl = import.meta.env.VITE_BACKEND_URL;
  const body = {
    story_text: storyText,
    character_name: characterName || undefined,
    preferred_model: preferredModel,
    content_rating: contentRating,
    extra_instructions: extraInstructions || undefined,
  };

  // When VITE_BACKEND_URL is set, use full absolute URL (bypasses axios baseURL).
  // Otherwise use relative path (axios prepends baseURL: '/api').
  const { data } = backendUrl
    ? await api.post<Partial<Character>>(`${backendUrl}/api/characters/generate-from-story`, body, { timeout: 120_000 })
    : await api.post<Partial<Character>>('/characters/generate-from-story', body, { timeout: 120_000 });
  return data;
}
