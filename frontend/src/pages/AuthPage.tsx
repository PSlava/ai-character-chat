import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { signIn, signUp } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function AuthPage() {
  const { t } = useTranslation();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { init } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isLogin) {
        await signIn(email, password);
      } else {
        await signUp(email, password, username);
      }
      init(); // refresh auth state
      navigate('/');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || t('auth.error'));
      } else {
        setError(t('auth.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">
            {isLogin ? t('auth.login') : t('auth.register')}
          </h1>
          <p className="text-neutral-400 mt-1">
            {isLogin
              ? t('auth.loginSubtitle')
              : t('auth.registerSubtitle')}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <Input
              label={t('auth.username')}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="username"
              required
            />
          )}
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
          <Input
            label={t('auth.password')}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            minLength={6}
          />

          {error && (
            <p className="text-red-400 text-sm">{error}</p>
          )}

          <Button type="submit" disabled={loading} className="w-full">
            {loading
              ? t('common.loading')
              : isLogin
                ? t('auth.loginButton')
                : t('auth.registerButton')}
          </Button>
        </form>

        <p className="text-center text-sm text-neutral-400">
          {isLogin ? t('auth.noAccount') : t('auth.hasAccount')}{' '}
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            className="text-purple-400 hover:text-purple-300"
          >
            {isLogin ? t('auth.switchToRegister') : t('auth.switchToLogin')}
          </button>
        </p>
      </div>
    </div>
  );
}
