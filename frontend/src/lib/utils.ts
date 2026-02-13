export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  });
}

export function isCharacterOnline(characterId: string): boolean {
  const hour = new Date().getHours();
  let hash = hour;
  for (let i = 0; i < characterId.length; i++) {
    hash = ((hash << 5) - hash + characterId.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % 3 === 0;
}
