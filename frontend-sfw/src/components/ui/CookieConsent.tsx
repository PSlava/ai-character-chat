import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { localePath } from '@/lib/lang';

const STORAGE_KEY = 'cookie-consent';

export function CookieConsent() {
  const { t } = useTranslation();
  const [accepted, setAccepted] = useState(() => localStorage.getItem(STORAGE_KEY) === '1');

  if (accepted) return null;

  const handleAccept = () => {
    localStorage.setItem(STORAGE_KEY, '1');
    setAccepted(true);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 sm:p-0">
      <div className="mx-auto max-w-xl sm:mb-6 bg-neutral-900 border border-neutral-700 rounded-xl p-4 shadow-2xl flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <p className="text-sm text-neutral-300 flex-1">
          {t('cookie.message')}{' '}
          <Link to={localePath('/privacy')} className="text-blue-400 hover:text-blue-300 underline">
            {t('cookie.learnMore')}
          </Link>
        </p>
        <button
          onClick={handleAccept}
          className="shrink-0 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {t('cookie.accept')}
        </button>
      </div>
    </div>
  );
}
