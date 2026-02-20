import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, X } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function InstallPrompt() {
  const { t } = useTranslation();
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Don't show if already dismissed or installed
    if (localStorage.getItem('pwa-dismissed')) return;
    if (window.matchMedia('(display-mode: standalone)').matches) return;

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setShow(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  if (!show || !deferredPrompt) return null;

  const handleInstall = async () => {
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShow(false);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShow(false);
    localStorage.setItem('pwa-dismissed', '1');
  };

  return (
    <div className="fixed bottom-16 left-4 right-4 z-50 sm:left-auto sm:right-4 sm:max-w-sm animate-slide-up">
      <div className="bg-neutral-800 border border-neutral-700 rounded-xl p-4 shadow-2xl">
        <div className="flex items-start gap-3">
          <div className="shrink-0 w-10 h-10 bg-rose-600 rounded-lg flex items-center justify-center">
            <Download size={20} className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">{t('pwa.install')}</p>
            <p className="text-xs text-neutral-400 mt-0.5">{t('pwa.installDescription')}</p>
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleInstall}
                className="px-4 py-1.5 text-xs font-medium bg-rose-600 hover:bg-rose-700 text-white rounded-lg transition-colors"
              >
                {t('pwa.installButton')}
              </button>
              <button
                onClick={handleDismiss}
                className="px-3 py-1.5 text-xs text-neutral-400 hover:text-white hover:bg-neutral-700 rounded-lg transition-colors"
              >
                {t('pwa.later')}
              </button>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="shrink-0 text-neutral-500 hover:text-neutral-300 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
