import { useTranslation } from 'react-i18next';
import { Swords, Shield, Heart, Skull, MapPin, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface Combatant {
  name: string;
  hp: number;
  max_hp: number;
  ac?: number;
  initiative?: number;
  conditions?: string[];
  is_player?: boolean;
}

interface EncounterState {
  combat?: boolean;
  round?: number;
  combatants?: Combatant[];
  current_turn?: number;
  location?: string;
  [key: string]: unknown;
}

export function EncounterPanel({ state }: { state: EncounterState }) {
  const { t } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);

  if (!state?.combat || !state.combatants?.length) return null;

  const hpPercent = (hp: number, max: number) => Math.max(0, Math.min(100, (hp / max) * 100));
  const hpColor = (pct: number) =>
    pct > 60 ? 'bg-green-500' : pct > 30 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="bg-neutral-800/80 border border-amber-500/20 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-amber-300 hover:bg-neutral-700/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Swords className="w-4 h-4" />
          <span>{t('game.combat', 'Combat')}</span>
          {state.round && (
            <span className="text-xs text-neutral-500">
              {t('game.round', 'Round')} {state.round}
            </span>
          )}
        </div>
        {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
      </button>

      {!collapsed && (
        <div className="px-3 pb-3 space-y-2">
          {/* Location */}
          {state.location && (
            <div className="flex items-center gap-1.5 text-xs text-neutral-400">
              <MapPin className="w-3 h-3" />
              <span>{state.location}</span>
            </div>
          )}

          {/* Combatants */}
          {state.combatants.map((c, i) => {
            const pct = hpPercent(c.hp, c.max_hp);
            const isDead = c.hp <= 0;
            return (
              <div
                key={`${c.name}-${i}`}
                className={`rounded-md p-2 ${
                  c.is_player
                    ? 'bg-purple-500/10 border border-purple-500/20'
                    : 'bg-neutral-700/50'
                } ${isDead ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    {isDead ? (
                      <Skull className="w-3.5 h-3.5 text-red-400" />
                    ) : c.is_player ? (
                      <Shield className="w-3.5 h-3.5 text-purple-400" />
                    ) : (
                      <Heart className="w-3.5 h-3.5 text-red-400" />
                    )}
                    <span className={`text-sm font-medium ${c.is_player ? 'text-purple-200' : 'text-neutral-300'}`}>
                      {c.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-neutral-500">
                    {c.ac && <span>AC {c.ac}</span>}
                    <span className={isDead ? 'text-red-400' : ''}>
                      {c.hp}/{c.max_hp}
                    </span>
                  </div>
                </div>
                {/* HP Bar */}
                <div className="h-1.5 bg-neutral-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${hpColor(pct)}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                {/* Conditions */}
                {c.conditions && c.conditions.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {c.conditions.map((cond) => (
                      <span
                        key={cond}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300"
                      >
                        {cond}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
