/**
 * Proof-of-Work solver for registration anti-bot protection.
 * Finds a nonce such that SHA256(challenge + nonce) starts with `difficulty` hex zeros.
 * ~50-200ms in browser for difficulty=4.
 */
export async function solveChallenge(challenge: string, difficulty = 4): Promise<string> {
  const target = '0'.repeat(difficulty);
  for (let nonce = 0; ; nonce++) {
    const data = new TextEncoder().encode(challenge + nonce);
    const hash = await crypto.subtle.digest('SHA-256', data);
    const hex = [...new Uint8Array(hash)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    if (hex.startsWith(target)) return String(nonce);
  }
}
