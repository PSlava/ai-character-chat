import { create } from 'zustand';
import type { Chat } from '@/types';
import * as chatApi from '@/api/chat';

interface ChatState {
  chats: Chat[];
  loading: boolean;
  fetchChats: () => Promise<void>;
  removeChat: (id: string) => void;
}

// Deduplication: prevent concurrent fetches
let _fetchPromise: Promise<void> | null = null;

export const useChatStore = create<ChatState>((set, get) => ({
  chats: [],
  loading: false,

  fetchChats: async () => {
    // Dedup: if already fetching, return existing promise
    if (_fetchPromise) return _fetchPromise;

    // Stale-while-revalidate: show existing data while refreshing
    const hasData = get().chats.length > 0;
    if (!hasData) set({ loading: true });

    _fetchPromise = chatApi.getChats()
      .then((chats) => set({ chats, loading: false }))
      .catch(() => set({ loading: false }))
      .finally(() => { _fetchPromise = null; });

    return _fetchPromise;
  },

  removeChat: (id) => {
    set((state) => ({ chats: state.chats.filter((c) => c.id !== id) }));
  },
}));
