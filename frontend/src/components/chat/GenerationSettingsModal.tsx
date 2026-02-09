import { useState } from 'react';
import { X } from 'lucide-react';
import type { GenerationSettings } from '@/hooks/useChat';
import type { OpenRouterModel } from '@/api/characters';

export interface ChatSettings extends GenerationSettings {
  model?: string;
}

interface Props {
  settings: ChatSettings;
  currentModel: string;
  orModels: OpenRouterModel[];
  onApply: (settings: ChatSettings) => void;
  onClose: () => void;
}

function Slider({
  label,
  tooltip,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  tooltip: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-neutral-200">{label}</span>
          <span className="text-neutral-500 cursor-help" title={tooltip}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </span>
        </div>
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="w-16 bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm text-white text-right"
        />
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full accent-purple-500"
      />
    </div>
  );
}

const GEN_DEFAULTS = {
  temperature: 0.8,
  top_p: 0.95,
  top_k: 0,
  frequency_penalty: 0,
};

interface ModelOption {
  id: string;
  label: string;
  group: 'free' | 'direct' | 'paid';
}

const BUILTIN_MODELS: ModelOption[] = [
  { id: 'openrouter', label: 'OpenRouter Auto (Free)', group: 'free' },
  { id: 'deepseek', label: 'DeepSeek', group: 'direct' },
  { id: 'qwen', label: 'Qwen', group: 'direct' },
  { id: 'gemini', label: 'Gemini', group: 'paid' },
  { id: 'claude', label: 'Claude', group: 'paid' },
  { id: 'openai', label: 'GPT-4o', group: 'paid' },
];

export function GenerationSettingsModal({ settings, currentModel, orModels, onApply, onClose }: Props) {
  const [model, setModel] = useState(settings.model || currentModel);
  const [local, setLocal] = useState({
    temperature: settings.temperature ?? GEN_DEFAULTS.temperature,
    top_p: settings.top_p ?? GEN_DEFAULTS.top_p,
    top_k: settings.top_k ?? GEN_DEFAULTS.top_k,
    frequency_penalty: settings.frequency_penalty ?? GEN_DEFAULTS.frequency_penalty,
  });

  const update = <K extends keyof typeof GEN_DEFAULTS>(key: K, value: number) =>
    setLocal((prev) => ({ ...prev, [key]: value }));

  // Build full model list: OpenRouter models grouped with builtins
  const allModels: ModelOption[] = [
    ...BUILTIN_MODELS.filter((m) => m.group === 'free'),
    ...orModels.map((m) => ({ id: m.id, label: `${m.name} (${m.quality}/10)`, group: 'free' as const })),
    ...BUILTIN_MODELS.filter((m) => m.group === 'direct'),
    ...BUILTIN_MODELS.filter((m) => m.group === 'paid'),
  ];

  const isSelected = (id: string) => model === id;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Модель и настройки</h2>
          <button onClick={onClose} className="p-1 text-neutral-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Model selection */}
        <div className="mb-6">
          <p className="text-sm text-neutral-400 mb-3">Выбор модели для генерации ответа</p>
          <div className="grid grid-cols-2 gap-2">
            {allModels.map((m) => (
              <button
                key={m.id}
                onClick={() => setModel(m.id)}
                className={`text-left px-3 py-2.5 rounded-lg border text-sm transition-colors ${
                  isSelected(m.id)
                    ? 'border-purple-500 bg-purple-500/10 text-white'
                    : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                }`}
              >
                <span className="block font-medium truncate">{m.label}</span>
                <span className="block text-xs text-neutral-500 mt-0.5">
                  {m.group === 'free' ? 'Бесплатно' : m.group === 'direct' ? 'Прямой API' : 'Платная'}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Generation params */}
        <div className="space-y-5">
          <Slider
            label="Температура"
            tooltip="Чем выше — тем более творческие и разнообразные ответы. Чем ниже — тем более предсказуемые."
            value={local.temperature}
            onChange={(v) => update('temperature', v)}
            min={0}
            max={2}
            step={0.01}
          />
          <Slider
            label="Top-P"
            tooltip="Nucleus sampling. Модель выбирает из токенов, суммарная вероятность которых не превышает это значение."
            value={local.top_p}
            onChange={(v) => update('top_p', v)}
            min={0}
            max={1}
            step={0.01}
          />
          <Slider
            label="Top-K"
            tooltip="Модель выбирает из K наиболее вероятных токенов. 0 = отключено."
            value={local.top_k}
            onChange={(v) => update('top_k', Math.round(v))}
            min={0}
            max={100}
            step={1}
          />
          <Slider
            label="Штраф за повторения"
            tooltip="Frequency penalty. Чем выше — тем реже модель повторяет одни и те же фразы."
            value={local.frequency_penalty}
            onChange={(v) => update('frequency_penalty', v)}
            min={0}
            max={2}
            step={0.01}
          />
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
          >
            Отмена
          </button>
          <button
            onClick={() => { onApply({ ...local, model }); onClose(); }}
            className="flex-1 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Применить
          </button>
        </div>
      </div>
    </div>
  );
}
