import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { setToken, setUser } from '@/lib/supabase';
import { useAuthStore } from '@/store/authStore';

export function OAuthCallbackPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { init } = useAuthStore();

  useEffect(() => {
    const token = params.get('token');
    const id = params.get('id');
    const email = params.get('email');
    const username = params.get('username');
    const role = params.get('role') || 'user';

    if (token && id && email && username) {
      setToken(token);
      setUser({ id, email, username, role });
      init();
      navigate('/', { replace: true });
    } else {
      navigate('/auth', { replace: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-full flex items-center justify-center">
      <p className="text-neutral-400">{t('auth.oauthProcessing')}</p>
    </div>
  );
}
