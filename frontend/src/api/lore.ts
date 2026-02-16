import api from './client';

export interface LoreEntry {
  id: string;
  character_id: string;
  keywords: string;
  content: string;
  enabled: boolean;
  position: number;
  created_at: string;
}

export async function getLoreEntries(characterId: string): Promise<LoreEntry[]> {
  const { data } = await api.get<LoreEntry[]>(`/characters/${characterId}/lore`);
  return data;
}

export async function createLoreEntry(
  characterId: string,
  body: { keywords: string; content: string; enabled?: boolean; position?: number },
): Promise<LoreEntry> {
  const { data } = await api.post<LoreEntry>(`/characters/${characterId}/lore`, body);
  return data;
}

export async function updateLoreEntry(
  characterId: string,
  entryId: string,
  body: { keywords?: string; content?: string; enabled?: boolean; position?: number },
): Promise<LoreEntry> {
  const { data } = await api.put<LoreEntry>(`/characters/${characterId}/lore/${entryId}`, body);
  return data;
}

export async function deleteLoreEntry(characterId: string, entryId: string): Promise<void> {
  await api.delete(`/characters/${characterId}/lore/${entryId}`);
}
