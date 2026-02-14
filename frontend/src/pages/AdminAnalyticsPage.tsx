import { useState, useEffect, useMemo } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/hooks/useAuth';
import { getAnalyticsOverview } from '@/api/analytics';
import type { AnalyticsOverview } from '@/api/analytics';
import { Avatar } from '@/components/ui/Avatar';
import {
  Users, UserPlus, Eye, Globe, MessageCircle, MessagesSquare,
  Smartphone, Monitor, Tablet,
} from 'lucide-react';

const PERIOD_OPTIONS = [
  { days: 1, label: '1d' },
  { days: 7, label: '7d' },
  { days: 30, label: '30d' },
  { days: 90, label: '90d' },
];

export function AdminAnalyticsPage() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    if (!isAdmin) return;
    setLoadingData(true);
    getAnalyticsOverview(days)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoadingData(false));
  }, [isAdmin, days]);

  if (loading) return null;
  if (!isAdmin) return <Navigate to="/" replace />;

  const s = data?.summary;

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{t('admin.analyticsTitle')}</h1>
          <p className="text-neutral-400 text-sm mt-1">{t('admin.analyticsSubtitle')}</p>
        </div>
        <div className="flex gap-1 bg-neutral-800/50 rounded-lg p-1">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.days}
              onClick={() => setDays(opt.days)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                days === opt.days
                  ? 'bg-rose-600 text-white'
                  : 'text-neutral-400 hover:text-white'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loadingData ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-neutral-800/50 rounded-xl p-4 animate-pulse h-24" />
          ))}
        </div>
      ) : !data ? (
        <p className="text-neutral-500 text-center py-12">{t('admin.analyticsError')}</p>
      ) : (
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <SummaryCard icon={<Users className="w-4 h-4" />} label={t('admin.analyticsUsers')} value={s?.users_total ?? 0} />
            <SummaryCard icon={<UserPlus className="w-4 h-4" />} label={t('admin.analyticsNewUsers')} value={s?.users_new ?? 0} accent />
            <SummaryCard icon={<Eye className="w-4 h-4" />} label={t('admin.analyticsPageviews')} value={s?.pageviews ?? 0} />
            <SummaryCard icon={<Globe className="w-4 h-4" />} label={t('admin.analyticsUnique')} value={s?.unique_visitors ?? 0} accent />
            <SummaryCard icon={<MessageCircle className="w-4 h-4" />} label={t('admin.analyticsMessages')} value={s?.messages ?? 0} />
            <SummaryCard icon={<MessagesSquare className="w-4 h-4" />} label={t('admin.analyticsChats')} value={s?.new_chats ?? 0} />
          </div>

          {/* Daily chart */}
          <DailyChart daily={data.daily} />

          {/* Two-column layout */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Top pages */}
            <Section title={t('admin.analyticsTopPages')}>
              {data.top_pages.length === 0 ? (
                <EmptyState />
              ) : (
                <table className="w-full text-sm">
                  <thead><tr className="text-neutral-500 text-xs">
                    <th className="text-left pb-2">{t('admin.analyticsPath')}</th>
                    <th className="text-right pb-2">{t('admin.analyticsViews')}</th>
                    <th className="text-right pb-2">{t('admin.analyticsUniq')}</th>
                  </tr></thead>
                  <tbody>
                    {data.top_pages.slice(0, 10).map((p) => (
                      <tr key={p.path} className="border-t border-neutral-800/50">
                        <td className="py-1.5 text-neutral-300 truncate max-w-[200px]">{p.path}</td>
                        <td className="py-1.5 text-right text-neutral-400">{p.views}</td>
                        <td className="py-1.5 text-right text-neutral-400">{p.unique}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Section>

            {/* Top referrers */}
            <Section title={t('admin.analyticsTopReferrers')}>
              {data.top_referrers.length === 0 ? (
                <EmptyState />
              ) : (
                <table className="w-full text-sm">
                  <thead><tr className="text-neutral-500 text-xs">
                    <th className="text-left pb-2">{t('admin.analyticsSource')}</th>
                    <th className="text-right pb-2">{t('admin.analyticsViews')}</th>
                  </tr></thead>
                  <tbody>
                    {data.top_referrers.slice(0, 10).map((r) => (
                      <tr key={r.referrer} className="border-t border-neutral-800/50">
                        <td className="py-1.5 text-neutral-300 truncate max-w-[250px]">{r.referrer}</td>
                        <td className="py-1.5 text-right text-neutral-400">{r.views}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Section>
          </div>

          {/* Two-column: characters + models */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Top characters */}
            <Section title={t('admin.analyticsTopChars')}>
              {data.top_characters.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-2">
                  {data.top_characters.map((c) => {
                    const maxMsg = data.top_characters[0]?.messages || 1;
                    return (
                      <div key={c.id} className="flex items-center gap-3">
                        <Avatar src={c.avatar_url} name={c.name} size="sm" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-neutral-300 truncate">{c.name}</div>
                          <div className="h-1.5 bg-neutral-800 rounded-full mt-1">
                            <div
                              className="h-full bg-rose-500/70 rounded-full"
                              style={{ width: `${(c.messages / maxMsg) * 100}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-xs text-neutral-500 tabular-nums">{c.messages}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </Section>

            {/* Devices + Models */}
            <div className="space-y-6">
              {/* Devices */}
              <Section title={t('admin.analyticsDevices')}>
                <DevicePills devices={data.devices} />
              </Section>

              {/* Models */}
              <Section title={t('admin.analyticsModels')}>
                {data.models.length === 0 ? (
                  <EmptyState />
                ) : (
                  <div className="space-y-1.5">
                    {data.models.slice(0, 8).map((m) => {
                      const maxCount = data.models[0]?.count || 1;
                      return (
                        <div key={m.model} className="flex items-center gap-2">
                          <span className="text-xs text-neutral-400 truncate w-40">{m.model}</span>
                          <div className="flex-1 h-1.5 bg-neutral-800 rounded-full">
                            <div
                              className="h-full bg-neutral-500/70 rounded-full"
                              style={{ width: `${(m.count / maxCount) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-neutral-500 tabular-nums w-8 text-right">{m.count}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Section>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Sub-components ---

function SummaryCard({ icon, label, value, accent }: {
  icon: React.ReactNode; label: string; value: number; accent?: boolean;
}) {
  return (
    <div className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
      <div className="flex items-center gap-1.5 text-neutral-500 text-xs mb-2">
        {icon}
        {label}
      </div>
      <div className={`text-2xl font-bold tabular-nums ${accent ? 'text-rose-400' : 'text-neutral-200'}`}>
        {value.toLocaleString()}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-neutral-800/30 border border-neutral-700/50 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-neutral-300 mb-3">{title}</h3>
      {children}
    </div>
  );
}

function EmptyState() {
  const { t } = useTranslation();
  return <p className="text-neutral-600 text-sm py-4 text-center">{t('admin.analyticsNoData')}</p>;
}

function DailyChart({ daily }: { daily: AnalyticsOverview['daily'] }) {
  const { t } = useTranslation();
  const maxPV = useMemo(() => Math.max(1, ...daily.map((d) => d.pageviews)), [daily]);

  if (daily.length === 0) return null;

  return (
    <Section title={t('admin.analyticsDailyTraffic')}>
      <div className="flex items-end gap-[2px] h-32">
        {daily.map((d) => {
          const pvH = (d.pageviews / maxPV) * 100;
          const uvH = (d.unique_visitors / maxPV) * 100;
          const dayLabel = d.date.slice(5); // "02-08"
          return (
            <div
              key={d.date}
              className="flex-1 flex flex-col items-center gap-0.5 group relative"
            >
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-10 bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-xs whitespace-nowrap shadow-lg">
                <div className="font-semibold text-neutral-200 mb-1">{d.date}</div>
                <div className="text-neutral-400">{t('admin.analyticsPageviews')}: {d.pageviews}</div>
                <div className="text-rose-400">{t('admin.analyticsUnique')}: {d.unique_visitors}</div>
                <div className="text-neutral-400">{t('admin.analyticsRegistrations')}: {d.registrations}</div>
                <div className="text-neutral-400">{t('admin.analyticsMessages')}: {d.messages}</div>
              </div>
              {/* Bars */}
              <div className="w-full flex gap-[1px] items-end h-24">
                <div
                  className="flex-1 bg-neutral-600/50 rounded-t-sm min-h-[2px]"
                  style={{ height: `${Math.max(2, pvH)}%` }}
                />
                <div
                  className="flex-1 bg-rose-500/60 rounded-t-sm min-h-[2px]"
                  style={{ height: `${Math.max(2, uvH)}%` }}
                />
              </div>
              {/* Registration dot */}
              {d.registrations > 0 && (
                <div className="w-1.5 h-1.5 rounded-full bg-green-400" title={`${d.registrations} reg`} />
              )}
              {/* Day label (show every Nth depending on total) */}
              {daily.length <= 14 || daily.indexOf(d) % Math.ceil(daily.length / 14) === 0 ? (
                <span className="text-[9px] text-neutral-600 mt-1">{dayLabel}</span>
              ) : null}
            </div>
          );
        })}
      </div>
      {/* Legend */}
      <div className="flex gap-4 mt-3 text-xs text-neutral-500 justify-center">
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 bg-neutral-600/50 rounded-sm" />
          {t('admin.analyticsPageviews')}
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 bg-rose-500/60 rounded-sm" />
          {t('admin.analyticsUnique')}
        </span>
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-green-400 rounded-full" />
          {t('admin.analyticsRegistrations')}
        </span>
      </div>
    </Section>
  );
}

function DevicePills({ devices }: { devices: AnalyticsOverview['devices'] }) {
  const total = devices.mobile + devices.desktop + devices.tablet;
  if (total === 0) return <EmptyState />;
  const pct = (n: number) => total > 0 ? Math.round((n / total) * 100) : 0;

  return (
    <div className="flex gap-2">
      <DevicePill icon={<Monitor className="w-3.5 h-3.5" />} label="Desktop" count={devices.desktop} percent={pct(devices.desktop)} />
      <DevicePill icon={<Smartphone className="w-3.5 h-3.5" />} label="Mobile" count={devices.mobile} percent={pct(devices.mobile)} />
      <DevicePill icon={<Tablet className="w-3.5 h-3.5" />} label="Tablet" count={devices.tablet} percent={pct(devices.tablet)} />
    </div>
  );
}

function DevicePill({ icon, label, count, percent }: {
  icon: React.ReactNode; label: string; count: number; percent: number;
}) {
  return (
    <div className="flex-1 bg-neutral-800/50 rounded-lg px-3 py-2 text-center">
      <div className="flex items-center justify-center gap-1 text-neutral-400 mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className="text-lg font-bold text-neutral-200">{percent}%</div>
      <div className="text-xs text-neutral-500">{count}</div>
    </div>
  );
}
