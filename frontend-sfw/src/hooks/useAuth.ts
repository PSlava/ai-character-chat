import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const { token, user, loading, init } = useAuthStore();

  useEffect(() => {
    init();
  }, [init]);

  return { user, loading, isAuthenticated: !!token };
}
