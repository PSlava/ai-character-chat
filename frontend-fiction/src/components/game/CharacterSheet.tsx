import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Shield, Heart, MapPin, ChevronDown, ChevronUp, Backpack, Scroll, Swords } from 'lucide-react';

interface PlayerData {
  name?: string;
  hp?: number;
  max_hp?: number;
  class?: string;
  level?: number;
  ac?: number;
  stats?: {
    str?: number;
    dex?: number;
    con?: number;
    int?: number;
    wis?: number;
    cha?: number;
  };
  inventory?: string[];
  conditions?: string[];
}

interface SheetState {
  player?: PlayerData;
  combat?: boolean;
  location?: string;
  [key: string]: unknown;
}

const STAT_LABELS = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'] as const;
const STAT_KEYS = ['str', 'dex', 'con', 'int', 'wis', 'cha'] as const;

function statMod(val: number): string {
  const mod = Math.floor((val - 10) / 2);
  return mod >= 0 ? `+${mod}` : `${mod}`;
}

export function CharacterSheet({ state }: { state: SheetState }) {
  const { t } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);
  const player = state?.player;

  if (!player) return null;

  const hpPct = player.hp != null && player.max_hp
    ? Math.max(0, Math.min(100, (player.hp / player.max_hp) * 100))
    : null;
  const hpColor = hpPct == null ? '' : hpPct > 60 ? 'bg-green-500' : hpPct > 30 ? 'bg-amber-500' : 'bg-red-500';

  const title = [
    player.name,
    player.class && player.level ? `${player.class} ${t('sheet.level', 'Lv.')} ${player.level}` : player.class,
  ].filter(Boolean).join(' — ');

  return (
    <div className="bg-neutral-800/80 border border-purple-500/20 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-purple-300 hover:bg-neutral-700/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Scroll className="w-4 h-4" />
          <span>{title || t('sheet.title', 'Character Sheet')}</span>
        </div>
        <div className="flex items-center gap-2">
          {state.combat && (
            <span className="flex items-center gap-1 text-xs text-amber-400">
              <Swords className="w-3 h-3" />
              {t('game.combat', 'Combat')}
            </span>
          )}
          {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </div>
      </button>

      {!collapsed && (
        <div className="px-3 pb-3 space-y-2.5">
          {/* HP Bar */}
          {player.hp != null && player.max_hp != null && (
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <div className="flex items-center gap-1 text-red-400">
                  <Heart className="w-3 h-3" />
                  <span>HP</span>
                </div>
                <div className="flex items-center gap-2 text-neutral-400">
                  {player.ac && (
                    <span className="flex items-center gap-0.5">
                      <Shield className="w-3 h-3" /> {player.ac}
                    </span>
                  )}
                  <span className={hpPct != null && hpPct <= 30 ? 'text-red-400' : ''}>
                    {player.hp}/{player.max_hp}
                  </span>
                </div>
              </div>
              <div className="h-2 bg-neutral-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${hpColor}`}
                  style={{ width: `${hpPct}%` }}
                />
              </div>
            </div>
          )}

          {/* Stats Grid */}
          {player.stats && (
            <div className="grid grid-cols-6 gap-1">
              {STAT_LABELS.map((label, i) => {
                const val = player.stats?.[STAT_KEYS[i]];
                if (val == null) return null;
                return (
                  <div key={label} className="text-center bg-neutral-700/50 rounded p-1">
                    <div className="text-[10px] text-neutral-500 uppercase">{label}</div>
                    <div className="text-sm font-medium text-neutral-200">{val}</div>
                    <div className="text-[10px] text-purple-400">{statMod(val)}</div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Conditions */}
          {player.conditions && player.conditions.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {player.conditions.map((c) => (
                <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                  {c}
                </span>
              ))}
            </div>
          )}

          {/* Inventory */}
          {player.inventory && player.inventory.length > 0 && (
            <div>
              <div className="flex items-center gap-1 text-xs text-neutral-500 mb-1">
                <Backpack className="w-3 h-3" />
                <span>{t('sheet.inventory', 'Inventory')}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {player.inventory.map((item) => (
                  <span key={item} className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-700/60 text-neutral-300">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Location */}
          {state.location && (
            <div className="flex items-center gap-1.5 text-xs text-neutral-400">
              <MapPin className="w-3 h-3" />
              <span>{state.location}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
