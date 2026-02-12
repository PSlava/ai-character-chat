import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { signIn, signUp, forgotPassword } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

type Mode = 'login' | 'register' | 'forgot';

const ERROR_MAP: Record<string, string> = {
  'Email already taken': 'auth.emailTaken',
  'Username already taken': 'auth.usernameTaken',
  'Invalid email or password': 'auth.invalidCredentials',
  'Username must be 3-20 characters: letters, digits, underscore': 'auth.usernameInvalid',
};

export function AuthPage() {
  const { t } = useTranslation();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const navigate = useNavigate();
  const { init } = useAuthStore();

  const switchMode = (m: Mode) => {
    setMode(m);
    setError('');
    setResetSent(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'forgot') {
        await forgotPassword(email);
        setResetSent(true);
      } else if (mode === 'login') {
        await signIn(email, password);
        init();
        navigate('/');
      } else {
        await signUp(email, password, username || undefined);
        init();
        navigate('/');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        const detail = axiosErr.response?.data?.detail || '';
        const key = ERROR_MAP[detail];
        setError(key ? t(key) : detail || t('auth.error'));
      } else {
        setError(t('auth.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const title = mode === 'forgot'
    ? t('auth.forgotPasswordTitle')
    : mode === 'login'
      ? t('auth.login')
      : t('auth.register');

  const subtitle = mode === 'forgot'
    ? t('auth.forgotPasswordSubtitle')
    : mode === 'login'
      ? t('auth.loginSubtitle')
      : t('auth.registerSubtitle');

  return (
    <div className="min-h-full flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="text-neutral-400 mt-1">{subtitle}</p>
        </div>

        {mode === 'forgot' && resetSent ? (
          <div className="space-y-4 text-center">
            <p className="text-neutral-300 text-sm">{t('auth.resetLinkSent')}</p>
            <button
              onClick={() => switchMode('login')}
              className="text-rose-400 hover:text-rose-300 text-sm"
            >
              {t('auth.backToLogin')}
            </button>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <Input
                  label={t('auth.username')}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={t('auth.usernameOptional')}
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
              {mode !== 'forgot' && (
                <Input
                  label={t('auth.password')}
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              )}

              {mode === 'login' && (
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => switchMode('forgot')}
                    className="text-sm text-neutral-400 hover:text-rose-400"
                  >
                    {t('auth.forgotPassword')}
                  </button>
                </div>
              )}

              {error && (
                <p className="text-red-400 text-sm">{error}</p>
              )}

              <Button type="submit" disabled={loading} className="w-full">
                {loading
                  ? t('common.loading')
                  : mode === 'forgot'
                    ? t('auth.sendResetLink')
                    : mode === 'login'
                      ? t('auth.loginButton')
                      : t('auth.registerButton')}
              </Button>
            </form>

            <p className="text-center text-sm text-neutral-400">
              {mode === 'forgot' ? (
                <button
                  onClick={() => switchMode('login')}
                  className="text-rose-400 hover:text-rose-300"
                >
                  {t('auth.backToLogin')}
                </button>
              ) : mode === 'login' ? (
                <>
                  {t('auth.noAccount')}{' '}
                  <button
                    onClick={() => switchMode('register')}
                    className="text-rose-400 hover:text-rose-300"
                  >
                    {t('auth.switchToRegister')}
                  </button>
                </>
              ) : (
                <>
                  {t('auth.hasAccount')}{' '}
                  <button
                    onClick={() => switchMode('login')}
                    className="text-rose-400 hover:text-rose-300"
                  >
                    {t('auth.switchToLogin')}
                  </button>
                </>
              )}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
