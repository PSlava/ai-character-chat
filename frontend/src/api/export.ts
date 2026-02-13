import api from './client';

export function getExportUrl(characterId: string): string {
  return `/api/characters/${characterId}/export`;
}

export async function importCharacter(card: object) {
  const { data } = await api.post<{ id: string; name: string }>('/characters/import', card);
  return data;
}
