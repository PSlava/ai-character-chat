import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useFavoritesStore } from '@/store/favoritesStore';
import { CharacterGrid } from '@/components/characters/CharacterGrid';
import { Heart } from 'lucide-react';
import { SEO } from '@/components/seo/SEO';

export function FavoritesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { favorites, loaded, fetchFavorites } = useFavoritesStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth');
      return;
    }
    fetchFavorites();
  }, [isAuthenticated, navigate, fetchFavorites]);

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      <SEO title={t('favorites.title')} />
      <h1 className="text-2xl font-bold mb-6">{t('favorites.title')}</h1>

      {!loaded ? (
        <CharacterGrid characters={[]} loading />
      ) : favorites.length === 0 ? (
        <div className="text-center py-16">
          <Heart className="w-12 h-12 text-neutral-700 mx-auto mb-4" />
          <p className="text-neutral-400 text-lg">{t('favorites.empty')}</p>
          <p className="text-neutral-500 text-sm mt-2">{t('favorites.emptyHint')}</p>
        </div>
      ) : (
        <CharacterGrid characters={favorites} />
      )}
    </div>
  );
}
