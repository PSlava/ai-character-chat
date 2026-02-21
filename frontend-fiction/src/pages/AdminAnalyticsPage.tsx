import { useState, useEffect, useMemo } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/hooks/useAuth';
import { getAnalyticsOverview, getCostAnalytics } from '@/api/analytics';
import type { AnalyticsOverview, CostAnalytics } from '@/api/analytics';
import { Avatar } from '@/components/ui/Avatar';
import {
  Users, UserPlus, Eye, Globe, MessageCircle, MessagesSquare,
  Smartphone, Monitor, Tablet, Bot, Coins,
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
  const [costData, setCostData] = useState<CostAnalytics | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [days, setDays] = useState(7);
  const [tab, setTab] = useState<'traffic' | 'costs'>('traffic');

  useEffect(() => {
    if (!isAdmin) return;
    setLoadingData(true);
    Promise.all([
      getAnalyticsOverview(days).catch(() => null),
      getCostAnalytics(days).catch(() => null),
    ]).then(([overview, costs]) => {
      setData(overview);
      setCostData(costs);
    }).finally(() => setLoadingData(false));
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
        <div className="flex items-center gap-3">
          {/* Tab switcher */}
          <div className="flex gap-1 bg-neutral-800/50 rounded-lg p-1">
            <button
              onClick={() => setTab('traffic')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === 'traffic' ? 'bg-neutral-700 text-white' : 'text-neutral-400 hover:text-white'
              }`}
            >
              Traffic
            </button>
            <button
              onClick={() => setTab('costs')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                tab === 'costs' ? 'bg-neutral-700 text-white' : 'text-neutral-400 hover:text-white'
              }`}
            >
              <Coins className="w-3.5 h-3.5" /> Costs
            </button>
          </div>
          {/* Period selector */}
          <div className="flex gap-1 bg-neutral-800/50 rounded-lg p-1">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.days}
                onClick={() => setDays(opt.days)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  days === opt.days
                    ? 'bg-purple-600 text-white'
                    : 'text-neutral-400 hover:text-white'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loadingData ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-neutral-800/50 rounded-xl p-4 animate-pulse h-24" />
          ))}
        </div>
      ) : tab === 'costs' ? (
        <CostsView data={costData} />
      ) : !data ? (
        <p className="text-neutral-500 text-center py-12">{t('admin.analyticsError')}</p>
      ) : (
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3">
            <SummaryCard icon={<Users className="w-4 h-4" />} label={t('admin.analyticsUsers')} value={s?.users_total ?? 0} />
            <SummaryCard icon={<UserPlus className="w-4 h-4" />} label={t('admin.analyticsNewUsers')} value={s?.users_new ?? 0} accent />
            <SummaryCard icon={<Eye className="w-4 h-4" />} label={t('admin.analyticsPageviews')} value={s?.pageviews ?? 0} />
            <SummaryCard icon={<Globe className="w-4 h-4" />} label={t('admin.analyticsUnique')} value={s?.unique_visitors ?? 0} accent />
            <SummaryCard icon={<MessageCircle className="w-4 h-4" />} label={t('admin.analyticsMessages')} value={s?.messages ?? 0} />
            <SummaryCard icon={<MessagesSquare className="w-4 h-4" />} label={t('admin.analyticsChats')} value={s?.new_chats ?? 0} />
            <SummaryCard icon={<Bot className="w-4 h-4" />} label={t('admin.analyticsBotViews')} value={data.bot_views?.views ?? 0} />
          </div>

          {/* Anonymous stats */}
          {data.anon_stats && (
            <Section title={t('admin.analyticsAnon')}>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <AnonStat label={t('admin.analyticsAnonSessionsNew')} value={data.anon_stats.unique_sessions} />
                <AnonStat label={t('admin.analyticsAnonSessionsTotal')} value={data.anon_stats.total_sessions} />
                <AnonStat label={t('admin.analyticsAnonMessages')} value={data.anon_stats.messages} />
                <AnonStat label={t('admin.analyticsAnonChats')} value={data.anon_stats.chats} />
                <AnonStat label={t('admin.analyticsAnonMessagesTotal')} value={data.anon_stats.total_messages} />
              </div>
            </Section>
          )}

          {/* Traffic Sources + OS */}
          <div className="grid md:grid-cols-2 gap-6">
            {data.traffic_sources && (
              <Section title={t('admin.analyticsTrafficSources')}>
                <TrafficSourceBars sources={data.traffic_sources} />
              </Section>
            )}
            {data.os && data.os.length > 0 && (
              <Section title={t('admin.analyticsOS')}>
                <OsPills items={data.os} />
              </Section>
            )}
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
                              className="h-full bg-purple-500/70 rounded-full"
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

            {/* Devices + Countries */}
            <div className="space-y-6">
              {/* Devices */}
              <Section title={t('admin.analyticsDevices')}>
                <DevicePills devices={data.devices} />
              </Section>

              {/* Countries */}
              <Section title={t('admin.analyticsCountries')}>
                {!data.countries || data.countries.length === 0 ? (
                  <EmptyState />
                ) : (
                  <div className="space-y-1.5">
                    {data.countries.slice(0, 10).map((c) => {
                      const maxUniq = data.countries[0]?.unique || 1;
                      return (
                        <div key={c.country} className="flex items-center gap-2">
                          <span className="text-sm w-7">{countryFlag(c.country)}</span>
                          <span className="text-xs text-neutral-400 w-8">{c.country}</span>
                          <div className="flex-1 h-1.5 bg-neutral-800 rounded-full">
                            <div
                              className="h-full bg-blue-500/60 rounded-full"
                              style={{ width: `${(c.unique / maxUniq) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-neutral-500 tabular-nums w-10 text-right">{c.unique}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Section>
            </div>

            {/* Models */}
            <div className="grid md:grid-cols-1 gap-6">
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

// --- Costs view ---

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

function CostsView({ data }: { data: CostAnalytics | null }) {
  if (!data) return <p className="text-neutral-500 text-center py-12">No cost data yet</p>;

  const { totals, daily, by_provider, top_users } = data;
  const maxDaily = Math.max(1, ...daily.map(d => d.total));

  return (
    <div className="space-y-6">
      {/* Totals */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
          <div className="text-xs text-neutral-500 mb-2">Total Tokens</div>
          <div className="text-2xl font-bold text-neutral-200 tabular-nums">{formatTokens(totals.total_tokens)}</div>
        </div>
        <div className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
          <div className="text-xs text-neutral-500 mb-2">Prompt Tokens</div>
          <div className="text-2xl font-bold text-blue-400 tabular-nums">{formatTokens(totals.prompt_tokens)}</div>
        </div>
        <div className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
          <div className="text-xs text-neutral-500 mb-2">Completion Tokens</div>
          <div className="text-2xl font-bold text-green-400 tabular-nums">{formatTokens(totals.completion_tokens)}</div>
        </div>
        <div className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4">
          <div className="text-xs text-neutral-500 mb-2">Messages</div>
          <div className="text-2xl font-bold text-neutral-200 tabular-nums">{totals.messages.toLocaleString()}</div>
        </div>
      </div>

      {/* Daily token chart */}
      {daily.length > 0 && (
        <Section title="Daily Token Usage">
          <div className="flex items-end gap-[2px] h-32">
            {daily.map((d) => {
              const pH = (d.prompt_tokens / maxDaily) * 100;
              const cH = (d.completion_tokens / maxDaily) * 100;
              const dayLabel = d.date.slice(5);
              return (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-0.5 group relative">
                  <div className="absolute bottom-full mb-2 hidden group-hover:block z-10 bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-xs whitespace-nowrap shadow-lg">
                    <div className="font-semibold text-neutral-200 mb-1">{d.date}</div>
                    <div className="text-blue-400">Prompt: {formatTokens(d.prompt_tokens)}</div>
                    <div className="text-green-400">Completion: {formatTokens(d.completion_tokens)}</div>
                    <div className="text-neutral-400">Total: {formatTokens(d.total)}</div>
                  </div>
                  <div className="w-full flex flex-col items-stretch h-24 justify-end">
                    <div
                      className="bg-blue-500/50 rounded-t-sm min-h-[1px]"
                      style={{ height: `${Math.max(1, pH)}%` }}
                    />
                    <div
                      className="bg-green-500/50 min-h-[1px]"
                      style={{ height: `${Math.max(1, cH)}%` }}
                    />
                  </div>
                  {daily.length <= 14 || daily.indexOf(d) % Math.ceil(daily.length / 14) === 0 ? (
                    <span className="text-[9px] text-neutral-600 mt-1">{dayLabel}</span>
                  ) : null}
                </div>
              );
            })}
          </div>
          <div className="flex gap-4 mt-3 text-xs text-neutral-500 justify-center">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-blue-500/50 rounded-sm" /> Prompt
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-green-500/50 rounded-sm" /> Completion
            </span>
          </div>
        </Section>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* By provider */}
        <Section title="Token Usage by Provider">
          {by_provider.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-2">
              {by_provider.map((p) => {
                const maxTotal = by_provider[0]?.total || 1;
                return (
                  <div key={p.provider} className="flex items-center gap-2">
                    <span className="text-xs text-neutral-400 w-20 truncate">{p.provider}</span>
                    <div className="flex-1 h-2 bg-neutral-800 rounded-full">
                      <div
                        className="h-full bg-amber-500/60 rounded-full"
                        style={{ width: `${(p.total / maxTotal) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-neutral-500 tabular-nums w-14 text-right">{formatTokens(p.total)}</span>
                    <span className="text-xs text-neutral-600 tabular-nums w-10 text-right">{p.messages}m</span>
                  </div>
                );
              })}
            </div>
          )}
        </Section>

        {/* Top users */}
        <Section title="Top Users by Tokens">
          {top_users.length === 0 ? (
            <EmptyState />
          ) : (
            <table className="w-full text-sm">
              <thead><tr className="text-neutral-500 text-xs">
                <th className="text-left pb-2">User</th>
                <th className="text-right pb-2">Msgs</th>
                <th className="text-right pb-2">Tokens</th>
              </tr></thead>
              <tbody>
                {top_users.map((u) => (
                  <tr key={u.user_id} className="border-t border-neutral-800/50">
                    <td className="py-1.5 text-neutral-300 truncate max-w-[150px]">{u.username}</td>
                    <td className="py-1.5 text-right text-neutral-400 tabular-nums">{u.messages}</td>
                    <td className="py-1.5 text-right text-neutral-400 tabular-nums">{formatTokens(u.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>
      </div>
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
      <div className={`text-2xl font-bold tabular-nums ${accent ? 'text-purple-400' : 'text-neutral-200'}`}>
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
                <div className="text-purple-400">{t('admin.analyticsUnique')}: {d.unique_visitors}</div>
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
                  className="flex-1 bg-purple-500/60 rounded-t-sm min-h-[2px]"
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
          <span className="w-2.5 h-2.5 bg-purple-500/60 rounded-sm" />
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

/** Convert 2-letter country code to flag emoji via regional indicator symbols */
function countryFlag(code: string): string {
  const upper = code.toUpperCase();
  if (upper.length !== 2) return upper;
  return String.fromCodePoint(
    ...Array.from(upper).map((c) => 0x1f1e6 + c.charCodeAt(0) - 65)
  );
}

function AnonStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <div className="text-xl font-bold text-amber-400 tabular-nums">{value.toLocaleString()}</div>
      <div className="text-xs text-neutral-500 mt-0.5">{label}</div>
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

const SOURCE_COLORS: Record<string, string> = {
  direct: 'bg-blue-500/70',
  organic: 'bg-green-500/70',
  social: 'bg-purple-500/70',
  referral: 'bg-amber-500/70',
};

const SOURCE_LABELS: Record<string, string> = {
  direct: 'Direct',
  organic: 'Organic',
  social: 'Social',
  referral: 'Referral',
};

function TrafficSourceBars({ sources }: { sources: AnalyticsOverview['traffic_sources'] }) {
  const { t } = useTranslation();
  const entries = Object.entries(sources.views) as [string, number][];
  const maxViews = Math.max(1, ...entries.map(([, v]) => v));
  const total = entries.reduce((acc, [, v]) => acc + v, 0);
  if (total === 0) return <EmptyState />;

  return (
    <div className="space-y-2">
      {entries.map(([key, views]) => {
        const uniq = sources.unique[key as keyof typeof sources.unique] ?? 0;
        const pct = total > 0 ? Math.round((views / total) * 100) : 0;
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="text-xs text-neutral-400 w-16">
              {t(`admin.analyticsSource_${key}`, SOURCE_LABELS[key] || key)}
            </span>
            <div className="flex-1 h-2 bg-neutral-800 rounded-full">
              <div
                className={`h-full rounded-full ${SOURCE_COLORS[key] || 'bg-neutral-500/70'}`}
                style={{ width: `${(views / maxViews) * 100}%` }}
              />
            </div>
            <span className="text-xs text-neutral-500 tabular-nums w-10 text-right">{pct}%</span>
            <span className="text-xs text-neutral-600 tabular-nums w-12 text-right">{uniq} uv</span>
          </div>
        );
      })}
    </div>
  );
}

function OsPills({ items }: { items: AnalyticsOverview['os'] }) {
  const total = items.reduce((acc, i) => acc + i.views, 0);
  if (total === 0) return <EmptyState />;
  const pct = (n: number) => total > 0 ? Math.round((n / total) * 100) : 0;

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <div key={item.os} className="bg-neutral-800/50 rounded-lg px-3 py-2 text-center min-w-[70px]">
          <div className="text-xs text-neutral-400 mb-1">{item.os}</div>
          <div className="text-lg font-bold text-neutral-200">{pct(item.views)}%</div>
          <div className="text-xs text-neutral-500">{item.views}</div>
        </div>
      ))}
    </div>
  );
}
