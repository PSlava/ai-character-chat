import { create } from 'zustand';
import * as usersApi from '@/api/users';
import type { Character } from '@/types';

interface FavoritesState {
  favoriteIds: Set<string>;
  favorites: Character[];
  loaded: boolean;
  fetchFavorites: () => Promise<void>;
  addFavorite: (characterId: string) => Promise<void>;
  removeFavorite: (characterId: string) => Promise<void>;
  clear: () => void;
}

export const useFavoritesStore = create<FavoritesState>((set, get) => ({
  favoriteIds: new Set(),
  favorites: [],
  loaded: false,

  fetchFavorites: async () => {
    try {
      const favorites = await usersApi.getFavorites();
      set({
        favorites,
        favoriteIds: new Set(favorites.map((c) => c.id)),
        loaded: true,
      });
    } catch {
      set({ loaded: true });
    }
  },

  addFavorite: async (characterId: string) => {
    const prev = get().favoriteIds;
    // Optimistic update
    set({ favoriteIds: new Set([...prev, characterId]) });
    try {
      await usersApi.addFavorite(characterId);
    } catch {
      // Rollback
      const rolled = new Set(prev);
      rolled.delete(characterId);
      set({ favoriteIds: rolled });
    }
  },

  removeFavorite: async (characterId: string) => {
    const prev = get().favoriteIds;
    const prevFavorites = get().favorites;
    // Optimistic update
    const next = new Set(prev);
    next.delete(characterId);
    set({
      favoriteIds: next,
      favorites: prevFavorites.filter((c) => c.id !== characterId),
    });
    try {
      await usersApi.removeFavorite(characterId);
    } catch {
      // Rollback
      set({ favoriteIds: prev, favorites: prevFavorites });
    }
  },

  clear: () => set({ favoriteIds: new Set(), favorites: [], loaded: false }),
}));
