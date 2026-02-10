import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
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
  groqModels: OpenRouterModel[];
  cerebrasModels: OpenRouterModel[];
  contentRating?: string;
  onApply: (settings: ChatSettings) => void;
  onClose: () => void;
}

function TooltipIcon({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const ref = useRef<HTMLSpanElement>(null);

  const open = () => {
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setPos({
        top: rect.top,
        left: Math.min(Math.max(12, rect.left - 120), window.innerWidth - 304),
      });
    }
    setShow(true);
  };
  const close = () => setShow(false);

  return (
    <span
      ref={ref}
      className="text-neutral-500 cursor-help"
      onMouseEnter={open}
      onMouseLeave={close}
      onClick={() => (show ? close() : open())}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      {show && pos && (
        <span
          className="fixed z-[100] w-72 max-w-[calc(100vw-24px)] p-3 bg-neutral-800 border border-neutral-600 rounded-lg text-xs text-neutral-300 leading-relaxed shadow-xl whitespace-pre-line pointer-events-none"
          style={{ bottom: `${window.innerHeight - pos.top + 8}px`, left: `${pos.left}px` }}
        >
          {text}
        </span>
      )}
    </span>
  );
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
          <TooltipIcon text={tooltip} />
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
  presence_penalty: 0.3,
  max_tokens: 2048,
  context_limit: 0,
};

const CONTEXT_OPTIONS = [
  { value: 4000, label: '4K' },
  { value: 8000, label: '8K' },
  { value: 16000, label: '16K' },
  { value: 0, label: '\u221E' }, // ∞
];

interface ModelOption {
  id: string;
  label: string;
  group: 'openrouter' | 'groq' | 'cerebras' | 'direct' | 'paid';
  nsfwOk?: boolean;
}

// GROUP_LABELS are now resolved via t() inside the component

export function GenerationSettingsModal({ settings, currentModel, orModels, groqModels, cerebrasModels, contentRating, onApply, onClose }: Props) {
  const { t } = useTranslation();
  const [model, setModel] = useState(settings.model || currentModel);
  const [local, setLocal] = useState({
    temperature: settings.temperature ?? GEN_DEFAULTS.temperature,
    top_p: settings.top_p ?? GEN_DEFAULTS.top_p,
    top_k: settings.top_k ?? GEN_DEFAULTS.top_k,
    frequency_penalty: settings.frequency_penalty ?? GEN_DEFAULTS.frequency_penalty,
    presence_penalty: settings.presence_penalty ?? GEN_DEFAULTS.presence_penalty,
    max_tokens: settings.max_tokens ?? GEN_DEFAULTS.max_tokens,
    context_limit: settings.context_limit ?? GEN_DEFAULTS.context_limit,
  });

  const update = <K extends keyof typeof GEN_DEFAULTS>(key: K, value: number) =>
    setLocal((prev) => ({ ...prev, [key]: value }));

  const isNsfw = contentRating === 'nsfw';

  // Build full model list with groups
  const allModels: ModelOption[] = [
    // OpenRouter
    { id: 'openrouter', label: 'OpenRouter Auto', group: 'openrouter', nsfwOk: true },
    ...orModels.map((m) => ({ id: m.id, label: `${m.name} (${m.quality}/10)`, group: 'openrouter' as const, nsfwOk: m.nsfw !== false })),
    // Groq
    { id: 'groq', label: 'Groq Auto', group: 'groq', nsfwOk: true },
    ...groqModels.map((m) => ({ id: `groq:${m.id}`, label: `${m.name} (${m.quality}/10)`, group: 'groq' as const, nsfwOk: m.nsfw !== false })),
    // Cerebras
    { id: 'cerebras', label: 'Cerebras Auto', group: 'cerebras', nsfwOk: true },
    ...cerebrasModels.map((m) => ({ id: `cerebras:${m.id}`, label: `${m.name} (${m.quality}/10)`, group: 'cerebras' as const, nsfwOk: m.nsfw !== false })),
    // Direct
    { id: 'deepseek', label: 'DeepSeek', group: 'direct', nsfwOk: true },
    { id: 'qwen', label: 'Qwen (DashScope)', group: 'direct', nsfwOk: false },
    // Paid
    { id: 'gemini', label: 'Gemini', group: 'paid', nsfwOk: true },
    { id: 'claude', label: 'Claude', group: 'paid', nsfwOk: true },
    { id: 'openai', label: 'GPT-4o', group: 'paid', nsfwOk: true },
  ];

  const isSelected = (id: string) => model === id;

  // Group models for rendering with headers
  const groups = ['openrouter', 'groq', 'cerebras', 'direct', 'paid'] as const;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">{t('settings.title')}</h2>
          <button onClick={onClose} className="p-1 text-neutral-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Model selection */}
        <div className="mb-6">
          <p className="text-sm text-neutral-400 mb-3">{t('settings.modelLabel')}</p>
          {groups.map((group) => {
            const items = allModels.filter((m) => m.group === group);
            if (items.length === 0) return null;
            return (
              <div key={group} className="mb-3">
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1.5">{t(`settings.group${group.charAt(0).toUpperCase()}${group.slice(1)}` as any)}</p>
                <div className="grid grid-cols-2 gap-2">
                  {items.map((m) => {
                    const disabled = isNsfw && !m.nsfwOk;
                    return (
                      <button
                        key={m.id}
                        onClick={() => !disabled && setModel(m.id)}
                        disabled={disabled}
                        className={`text-left px-3 py-2 rounded-lg border text-sm transition-colors ${
                          disabled
                            ? 'border-neutral-800 bg-neutral-800/50 text-neutral-600 cursor-not-allowed'
                            : isSelected(m.id)
                              ? 'border-purple-500 bg-purple-500/10 text-white'
                              : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                        }`}
                        title={disabled ? t('settings.nsfwBlocked') : undefined}
                      >
                        <span className="block font-medium truncate text-xs">{m.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Context memory */}
        <div className="mb-6">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-sm text-neutral-200">{t('settings.contextLimit')}</span>
            <TooltipIcon text={t('settings.contextLimitTooltip')} />
          </div>
          <div className="grid grid-cols-4 gap-2">
            {CONTEXT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => update('context_limit', opt.value)}
                className={`px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${
                  local.context_limit === opt.value
                    ? 'border-purple-500 bg-purple-500/10 text-white'
                    : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Generation params */}
        <div className="space-y-5">
          <Slider
            label={t('settings.temperature')}
            tooltip={t('settings.temperatureTooltip')}
            value={local.temperature}
            onChange={(v) => update('temperature', v)}
            min={0}
            max={2}
            step={0.01}
          />
          <Slider
            label={t('settings.topP')}
            tooltip={t('settings.topPTooltip')}
            value={local.top_p}
            onChange={(v) => update('top_p', v)}
            min={0}
            max={1}
            step={0.01}
          />
          <Slider
            label={t('settings.topK')}
            tooltip={t('settings.topKTooltip')}
            value={local.top_k}
            onChange={(v) => update('top_k', Math.round(v))}
            min={0}
            max={100}
            step={1}
          />
          <Slider
            label={t('settings.frequencyPenalty')}
            tooltip={t('settings.frequencyPenaltyTooltip')}
            value={local.frequency_penalty}
            onChange={(v) => update('frequency_penalty', v)}
            min={0}
            max={2}
            step={0.01}
          />
          <Slider
            label={t('settings.presencePenalty')}
            tooltip={t('settings.presencePenaltyTooltip')}
            value={local.presence_penalty}
            onChange={(v) => update('presence_penalty', v)}
            min={0}
            max={2}
            step={0.01}
          />
          <Slider
            label={t('settings.maxTokens')}
            tooltip={t('settings.maxTokensTooltip')}
            value={local.max_tokens}
            onChange={(v) => update('max_tokens', Math.round(v))}
            min={256}
            max={4096}
            step={128}
          />
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={() => { onApply({ ...local, model }); onClose(); }}
            className="flex-1 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {t('common.apply')}
          </button>
        </div>
      </div>
    </div>
  );
}
