import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { UserPlus } from 'lucide-react';

interface Props {
  onClose: () => void;
}

export function AnonLimitModal({ onClose }: Props) {
  const { t } = useTranslation();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="w-12 h-12 rounded-full bg-purple-600/20 flex items-center justify-center mx-auto mb-4">
          <UserPlus className="w-6 h-6 text-purple-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">
          {t('anon.limitTitle')}
        </h3>
        <p className="text-sm text-neutral-400 mb-6">
          {t('anon.limitMessage')}
        </p>
        <Link to="/auth">
          <Button size="lg" className="w-full mb-3">
            {t('anon.register')}
          </Button>
        </Link>
        <button
          onClick={onClose}
          className="text-sm text-neutral-500 hover:text-neutral-300 transition-colors"
        >
          {t('anon.later')}
        </button>
      </div>
    </div>
  );
}
