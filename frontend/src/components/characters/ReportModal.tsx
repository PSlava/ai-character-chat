import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import { createReport } from '@/api/reports';
import { Button } from '@/components/ui/Button';

interface Props {
  characterId: string;
  onClose: () => void;
}

const REASONS = ['spam', 'inappropriate', 'harassment', 'impersonation', 'other'] as const;

export function ReportModal({ characterId, onClose }: Props) {
  const { t } = useTranslation();
  const [reason, setReason] = useState<string>(REASONS[0]);
  const [details, setDetails] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await createReport(characterId, reason, details || undefined);
      toast.success(t('report.submitted'));
      onClose();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      const detail = ax?.response?.data?.detail || '';
      if (detail.includes('already have a pending')) {
        toast.error(t('report.alreadyReported'));
      } else {
        toast.error(detail || t('toast.networkError'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-2xl p-5 sm:p-6 w-full max-w-sm mx-4 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold text-white mb-4">{t('report.title')}</h3>

        <div className="space-y-3">
          <div>
            <label className="block text-sm text-neutral-400 mb-1">{t('report.reason')}</label>
            <div className="space-y-1">
              {REASONS.map((r) => (
                <label
                  key={r}
                  className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                    reason === r ? 'bg-rose-600/20 text-rose-300' : 'hover:bg-neutral-800 text-neutral-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={r}
                    checked={reason === r}
                    onChange={() => setReason(r)}
                    className="accent-rose-500"
                  />
                  {t(`report.reason${r.charAt(0).toUpperCase() + r.slice(1)}`)}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">{t('report.details')}</label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder={t('report.detailsPlaceholder')}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg p-2 text-sm text-white resize-none h-20 focus:outline-none focus:border-rose-500"
              maxLength={500}
            />
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-sm text-neutral-400 hover:text-white transition-colors"
          >
            {t('common.cancel')}
          </button>
          <Button onClick={handleSubmit} disabled={loading} className="flex-1">
            {loading ? t('common.loading') : t('report.submit')}
          </Button>
        </div>
      </div>
    </div>
  );
}
