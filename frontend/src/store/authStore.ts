import { create } from 'zustand';
import { getToken, getUser, removeToken, removeUser } from '@/lib/supabase';
import { useFavoritesStore } from './favoritesStore';
import { useVotesStore } from './votesStore';

interface AuthUser {
  id: string;
  email: string;
  username: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  init: () => void;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  loading: true,

  init: () => {
    const token = getToken();
    const user = getUser();
    set({ token, user, loading: false });
  },

  setAuth: (token, user) => {
    set({ token, user, loading: false });
  },

  logout: () => {
    removeToken();
    removeUser();
    useFavoritesStore.getState().clear();
    useVotesStore.getState().clear();
    set({ token: null, user: null });
  },
}));
