import { create } from 'zustand';
import type { GroupChat } from '@/api/groupChat';
import { getGroupChats } from '@/api/groupChat';

interface GroupChatState {
  groupChats: GroupChat[];
  loading: boolean;
  fetchGroupChats: () => Promise<void>;
  removeGroupChat: (id: string) => void;
  addGroupChat: (gc: GroupChat) => void;
}

let _fetchPromise: Promise<void> | null = null;

export const useGroupChatStore = create<GroupChatState>((set, get) => ({
  groupChats: [],
  loading: false,

  fetchGroupChats: async () => {
    if (_fetchPromise) return _fetchPromise;

    const hasData = get().groupChats.length > 0;
    if (!hasData) set({ loading: true });

    _fetchPromise = getGroupChats()
      .then((groupChats) => set({ groupChats, loading: false }))
      .catch(() => set({ loading: false }))
      .finally(() => { _fetchPromise = null; });

    return _fetchPromise;
  },

  removeGroupChat: (id) => {
    set((state) => ({ groupChats: state.groupChats.filter((gc) => gc.id !== id) }));
  },

  addGroupChat: (gc) => {
    set((state) => ({ groupChats: [gc, ...state.groupChats] }));
  },
}));
