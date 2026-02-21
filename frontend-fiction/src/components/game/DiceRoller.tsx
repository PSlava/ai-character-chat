import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Dices } from 'lucide-react';
import { rollDice } from '@/api/campaigns';
import type { DiceRollResult } from '@/types';

interface DiceRollerProps {
  onRollResult?: (result: DiceRollResult) => void;
}

export function DiceRoller({ onRollResult }: DiceRollerProps) {
  const { t } = useTranslation();
  const [expression, setExpression] = useState('d20');
  const [result, setResult] = useState<DiceRollResult | null>(null);
  const [rolling, setRolling] = useState(false);
  const [error, setError] = useState('');

  const handleRoll = async () => {
    if (!expression.trim() || rolling) return;
    setRolling(true);
    setError('');
    try {
      const res = await rollDice(expression.trim());
      setResult(res);
      onRollResult?.(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Roll failed');
    } finally {
      setRolling(false);
    }
  };

  const quickRolls = ['d20', '2d6', 'd20+5', '1d8+3', '2d20kh1'];

  return (
    <div className="bg-neutral-800/50 rounded-lg p-3 border border-neutral-700">
      <div className="flex items-center gap-2 mb-2">
        <Dices className="w-4 h-4 text-purple-400" />
        <span className="text-sm font-medium text-neutral-300">{t('game.diceRoller', 'Dice Roller')}</span>
      </div>

      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={expression}
          onChange={(e) => setExpression(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleRoll()}
          placeholder="d20, 2d6+3..."
          className="flex-1 bg-neutral-700 border border-neutral-600 rounded px-3 py-1.5 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-purple-500"
        />
        <button
          onClick={handleRoll}
          disabled={rolling}
          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded text-sm font-medium transition-colors"
        >
          {rolling ? '...' : t('game.roll', 'Roll')}
        </button>
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        {quickRolls.map((qr) => (
          <button
            key={qr}
            onClick={() => { setExpression(qr); }}
            className="px-2 py-0.5 text-xs bg-neutral-700 hover:bg-neutral-600 rounded text-neutral-400 hover:text-neutral-200 transition-colors"
          >
            {qr}
          </button>
        ))}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <DiceResultDisplay result={result} />
      )}
    </div>
  );
}

export function DiceResultDisplay({ result }: { result: DiceRollResult }) {
  return (
    <div className="bg-neutral-900/50 rounded p-2 border border-neutral-700">
      <div className="flex items-center justify-between">
        <span className="text-xs text-neutral-500">{result.expression}</span>
        <span className="text-lg font-bold text-purple-400">{result.total}</span>
      </div>
      <div className="flex items-center gap-1 text-xs text-neutral-500 mt-1">
        <span>[</span>
        {result.rolls.map((r, i) => (
          <span key={i} className={result.kept && !result.kept.includes(r) ? 'line-through text-neutral-600' : 'text-neutral-300'}>
            {r}{i < result.rolls.length - 1 ? ', ' : ''}
          </span>
        ))}
        <span>]</span>
        {result.modifier !== 0 && (
          <span className="text-neutral-400">
            {result.modifier > 0 ? '+' : ''}{result.modifier}
          </span>
        )}
      </div>
      {result.description && (
        <p className="text-xs text-neutral-400 mt-1 italic">{result.description}</p>
      )}
    </div>
  );
}
