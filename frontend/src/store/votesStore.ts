import { create } from 'zustand';
import { voteCharacter, getUserVotes } from '@/api/characters';

interface VotesState {
  votes: Record<string, number>; // characterId → +1|-1
  loaded: boolean;
  fetchVotes: () => Promise<void>;
  vote: (characterId: string, value: number) => Promise<{ vote_score: number } | null>;
  clear: () => void;
}

export const useVotesStore = create<VotesState>((set, get) => ({
  votes: {},
  loaded: false,

  fetchVotes: async () => {
    try {
      const votes = await getUserVotes();
      set({ votes, loaded: true });
    } catch {
      set({ loaded: true });
    }
  },

  vote: async (characterId: string, value: number) => {
    const prev = { ...get().votes };
    // Optimistic update
    if (value === 0) {
      const next = { ...prev };
      delete next[characterId];
      set({ votes: next });
    } else {
      set({ votes: { ...prev, [characterId]: value } });
    }
    try {
      const result = await voteCharacter(characterId, value);
      return result;
    } catch {
      // Rollback
      set({ votes: prev });
      return null;
    }
  },

  clear: () => set({ votes: {}, loaded: false }),
}));
