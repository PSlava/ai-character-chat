import { create } from 'zustand';
import type { Chat } from '@/types';
import * as chatApi from '@/api/chat';

interface ChatState {
  chats: Chat[];
  loading: boolean;
  fetchChats: () => Promise<void>;
  removeChat: (id: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  chats: [],
  loading: false,

  fetchChats: async () => {
    set({ loading: true });
    try {
      const chats = await chatApi.getChats();
      set({ chats, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  removeChat: (id) => {
    set((state) => ({ chats: state.chats.filter((c) => c.id !== id) }));
  },
}));
