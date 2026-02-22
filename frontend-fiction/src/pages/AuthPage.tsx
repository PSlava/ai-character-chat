import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { signIn, signUp, forgotPassword } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { SEO } from '@/components/seo/SEO';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import api from '@/api/client';

const RESET_COOLDOWN = 120; // 2 minutes, matches backend per-email limit

type Mode = 'login' | 'register' | 'forgot';

const ERROR_MAP: Record<string, string> = {
  'Email already taken': 'auth.emailTaken',
  'Username already taken': 'auth.usernameTaken',
  'Invalid email or password': 'auth.invalidCredentials',
  'Username must be 3-20 characters: letters, digits, underscore': 'auth.usernameInvalid',
  'Account is banned': 'auth.banned',
  'Too many requests. Try again later.': 'auth.tooManyRequests',
  'Too many registrations. Try again later.': 'auth.tooManyRegistrations',
  'Challenge required': 'auth.error',
  'Invalid challenge': 'auth.error',
  'Registration failed': 'auth.error',
};

export function AuthPage() {
  const { t } = useTranslation();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [username, setUsername] = useState('');
  const [honeypot, setHoneypot] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [googleOAuth, setGoogleOAuth] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval>>();
  const navigate = useNavigate();
  const { init } = useAuthStore();

  useEffect(() => {
    api.get('/auth/providers').then(r => setGoogleOAuth(r.data.google)).catch(() => {});
  }, []);

  const startCooldown = useCallback(() => {
    setCooldown(RESET_COOLDOWN);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, []);

  useEffect(() => () => clearInterval(timerRef.current), []);

  const switchMode = (m: Mode) => {
    setMode(m);
    setError('');
    setConfirmPassword('');
    setResetSent(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (mode === 'register' && password !== confirmPassword) {
      setError(t('auth.passwordsMismatch'));
      return;
    }
    setLoading(true);
    try {
      if (mode === 'forgot') {
        await forgotPassword(email);
        setResetSent(true);
        startCooldown();
      } else if (mode === 'login') {
        await signIn(email, password);
        init();
        navigate('/');
      } else {
        await signUp(email, password, username || undefined, honeypot || undefined);
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
      <SEO title={title} />
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="text-neutral-400 mt-1">{subtitle}</p>
        </div>

        {mode === 'forgot' && resetSent ? (
          <div className="space-y-4 text-center">
            <p className="text-neutral-300 text-sm">{t('auth.resetLinkSent')}</p>
            {cooldown > 0 ? (
              <p className="text-neutral-500 text-sm">
                {t('auth.resendIn', { seconds: cooldown })}
              </p>
            ) : (
              <button
                onClick={() => { setResetSent(false); setError(''); }}
                className="text-purple-400 hover:text-purple-300 text-sm"
              >
                {t('auth.resendResetLink')}
              </button>
            )}
            <button
              onClick={() => switchMode('login')}
              className="text-neutral-400 hover:text-neutral-300 text-sm"
            >
              {t('auth.backToLogin')}
            </button>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <>
                  <Input
                    label={t('auth.username')}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={t('auth.usernameOptional')}
                  />
                  <input
                    name="website"
                    value={honeypot}
                    onChange={(e) => setHoneypot(e.target.value)}
                    style={{ position: 'absolute', left: '-9999px' }}
                    tabIndex={-1}
                    autoComplete="off"
                    aria-hidden="true"
                  />
                </>
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
                <>
                  <Input
                    label={t('auth.password')}
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    minLength={6}
                  />
                  {mode === 'register' && (
                    <Input
                      label={t('auth.confirmPassword')}
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      minLength={6}
                    />
                  )}
                </>
              )}

              {mode === 'login' && (
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => switchMode('forgot')}
                    className="text-sm text-neutral-400 hover:text-purple-400"
                  >
                    {t('auth.forgotPassword')}
                  </button>
                </div>
              )}

              {error && (
                <p className="text-red-400 text-sm">{error}</p>
              )}

              <Button type="submit" disabled={loading || (mode === 'forgot' && cooldown > 0)} className="w-full">
                {loading
                  ? t('common.loading')
                  : mode === 'forgot'
                    ? cooldown > 0
                      ? t('auth.resendIn', { seconds: cooldown })
                      : t('auth.sendResetLink')
                    : mode === 'login'
                      ? t('auth.loginButton')
                      : t('auth.registerButton')}
              </Button>
            </form>

            {/* Google OAuth */}
            {googleOAuth && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-neutral-700" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-neutral-900 text-neutral-500">{t('auth.orDivider')}</span>
                  </div>
                </div>

                <a
                  href="/api/auth/google"
                  className="flex items-center justify-center gap-2 w-full px-4 py-2.5 border border-neutral-700 rounded-lg text-sm text-neutral-300 hover:border-neutral-500 hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  {t('auth.googleSignIn')}
                </a>
              </>
            )}

            <p className="text-center text-sm text-neutral-400">
              {mode === 'forgot' ? (
                <button
                  onClick={() => switchMode('login')}
                  className="text-purple-400 hover:text-purple-300"
                >
                  {t('auth.backToLogin')}
                </button>
              ) : mode === 'login' ? (
                <>
                  {t('auth.noAccount')}{' '}
                  <button
                    onClick={() => switchMode('register')}
                    className="text-purple-400 hover:text-purple-300"
                  >
                    {t('auth.switchToRegister')}
                  </button>
                </>
              ) : (
                <>
                  {t('auth.hasAccount')}{' '}
                  <button
                    onClick={() => switchMode('login')}
                    className="text-purple-400 hover:text-purple-300"
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
