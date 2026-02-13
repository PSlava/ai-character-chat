import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { getReports, updateReport } from '@/api/reports';
import type { Report } from '@/api/reports';
import { Avatar } from '@/components/ui/Avatar';
import toast from 'react-hot-toast';

const STATUSES = ['', 'pending', 'reviewed', 'dismissed'] as const;

export function AdminReportsPage() {
  const { t } = useTranslation();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAuthenticated || !isAdmin) return;
    setLoading(true);
    getReports(statusFilter || undefined)
      .then(setReports)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, isAdmin, statusFilter]);

  const handleUpdateStatus = async (reportId: string, status: string) => {
    try {
      await updateReport(reportId, status);
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? { ...r, status } : r))
      );
    } catch {
      toast.error(t('toast.networkError'));
    }
  };

  if (!authLoading && (!isAuthenticated || !isAdmin)) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-1">{t('admin.reportsTitle')}</h1>

      <div className="flex gap-2 mb-4 mt-3">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              statusFilter === s
                ? 'bg-rose-600 text-white'
                : 'bg-neutral-800 text-neutral-400 hover:text-white'
            }`}
          >
            {s ? t(`admin.reportStatus${s.charAt(0).toUpperCase() + s.slice(1)}`) : t('admin.reportStatusAll')}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-neutral-800/50 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <p className="text-neutral-500 text-sm">{t('home.noCharacters')}</p>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-4"
            >
              <div className="flex items-start gap-3">
                {report.character && (
                  <Link to={`/character/${report.character.id}`}>
                    <Avatar src={report.character.avatar_url} name={report.character.name} size="sm" />
                  </Link>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {report.character && (
                      <Link
                        to={`/character/${report.character.id}`}
                        className="font-medium text-white hover:text-rose-400 transition-colors"
                      >
                        {report.character.name}
                      </Link>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      report.status === 'pending'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : report.status === 'reviewed'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-neutral-600/20 text-neutral-400'
                    }`}>
                      {t(`admin.reportStatus${report.status.charAt(0).toUpperCase() + report.status.slice(1)}`)}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-300 mt-1">
                    <span className="text-neutral-500">{t('admin.reportReason')}:</span>{' '}
                    {t(`report.reason${report.reason.charAt(0).toUpperCase() + report.reason.slice(1)}`)}
                  </p>
                  {report.details && (
                    <p className="text-sm text-neutral-400 mt-1">{report.details}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-neutral-500">
                    {report.reporter && (
                      <span>{report.reporter.username} ({report.reporter.email})</span>
                    )}
                    <span>{new Date(report.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {report.status === 'pending' && (
                  <div className="flex gap-1 shrink-0">
                    <button
                      onClick={() => handleUpdateStatus(report.id, 'reviewed')}
                      className="px-2 py-1 text-xs bg-green-600/20 text-green-400 rounded hover:bg-green-600/30 transition-colors"
                    >
                      {t('admin.reportMarkReviewed')}
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(report.id, 'dismissed')}
                      className="px-2 py-1 text-xs bg-neutral-600/20 text-neutral-400 rounded hover:bg-neutral-600/30 transition-colors"
                    >
                      {t('admin.reportDismiss')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
