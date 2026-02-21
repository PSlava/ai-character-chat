import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/hooks/useAuth';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';

const STORAGE_KEY = 'age-verified';

export function AgeGate() {
  const { t } = useTranslation();
  const { isAuthenticated, loading } = useAuth();
  const [verified, setVerified] = useState(() => localStorage.getItem(STORAGE_KEY) === '1');

  if (loading || isAuthenticated || verified) return null;

  const handleConfirm = () => {
    localStorage.setItem(STORAGE_KEY, '1');
    setVerified(true);
  };

  const handleDecline = () => {
    window.location.href = 'https://google.com';
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-neutral-900 border border-neutral-700 rounded-2xl p-6 sm:p-8 w-full max-w-md mx-4 shadow-2xl text-center">
        <div className="flex justify-center mb-4">
          <LanguageSwitcher compact />
        </div>
        <div className="text-4xl mb-4">18+</div>
        <h2 className="text-xl font-bold text-white mb-2">{t('ageGate.title')}</h2>
        <p className="text-neutral-400 text-sm mb-6 leading-relaxed">{t('ageGate.message')}</p>
        <div className="flex flex-col gap-3">
          <button
            onClick={handleConfirm}
            className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            {t('ageGate.confirm')}
          </button>
          <button
            onClick={handleDecline}
            className="w-full px-6 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-400 rounded-lg text-sm font-medium transition-colors"
          >
            {t('ageGate.decline')}
          </button>
        </div>
        <p className="text-neutral-600 text-xs mt-4">{t('ageGate.disclaimer')}</p>
      </div>
    </div>
  );
}
