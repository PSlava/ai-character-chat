import { useState, useRef } from 'react';
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
  onApply: (settings: ChatSettings) => void;
  onClose: () => void;
}

function TooltipIcon({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  return (
    <span
      ref={ref}
      className="relative text-neutral-500 cursor-help"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onClick={() => setShow((v) => !v)}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      {show && (
        <span className="absolute z-50 left-1/2 -translate-x-1/2 bottom-full mb-2 w-72 p-3 bg-neutral-800 border border-neutral-600 rounded-lg text-xs text-neutral-300 leading-relaxed shadow-xl whitespace-pre-line">
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
  max_tokens: 2048,
};

interface ModelOption {
  id: string;
  label: string;
  group: 'openrouter' | 'groq' | 'cerebras' | 'direct' | 'paid';
}

const GROUP_LABELS: Record<string, string> = {
  openrouter: 'OpenRouter',
  groq: 'Groq',
  cerebras: 'Cerebras',
  direct: 'Прямой API',
  paid: 'Платные',
};

export function GenerationSettingsModal({ settings, currentModel, orModels, groqModels, cerebrasModels, onApply, onClose }: Props) {
  const [model, setModel] = useState(settings.model || currentModel);
  const [local, setLocal] = useState({
    temperature: settings.temperature ?? GEN_DEFAULTS.temperature,
    top_p: settings.top_p ?? GEN_DEFAULTS.top_p,
    top_k: settings.top_k ?? GEN_DEFAULTS.top_k,
    frequency_penalty: settings.frequency_penalty ?? GEN_DEFAULTS.frequency_penalty,
    max_tokens: settings.max_tokens ?? GEN_DEFAULTS.max_tokens,
  });

  const update = <K extends keyof typeof GEN_DEFAULTS>(key: K, value: number) =>
    setLocal((prev) => ({ ...prev, [key]: value }));

  // Build full model list with groups
  const allModels: ModelOption[] = [
    // OpenRouter
    { id: 'openrouter', label: 'OpenRouter Auto', group: 'openrouter' },
    ...orModels.map((m) => ({ id: m.id, label: `${m.name} (${m.quality}/10)`, group: 'openrouter' as const })),
    // Groq
    { id: 'groq', label: 'Groq Auto', group: 'groq' },
    ...groqModels.map((m) => ({ id: `groq:${m.id}`, label: `${m.name} (${m.quality}/10)`, group: 'groq' as const })),
    // Cerebras
    { id: 'cerebras', label: 'Cerebras Auto', group: 'cerebras' },
    ...cerebrasModels.map((m) => ({ id: `cerebras:${m.id}`, label: `${m.name} (${m.quality}/10)`, group: 'cerebras' as const })),
    // Direct
    { id: 'deepseek', label: 'DeepSeek', group: 'direct' },
    { id: 'qwen', label: 'Qwen (DashScope)', group: 'direct' },
    // Paid
    { id: 'gemini', label: 'Gemini', group: 'paid' },
    { id: 'claude', label: 'Claude', group: 'paid' },
    { id: 'openai', label: 'GPT-4o', group: 'paid' },
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
          <h2 className="text-lg font-bold">Модель и настройки</h2>
          <button onClick={onClose} className="p-1 text-neutral-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Model selection */}
        <div className="mb-6">
          <p className="text-sm text-neutral-400 mb-3">Выбор модели для генерации ответа</p>
          {groups.map((group) => {
            const items = allModels.filter((m) => m.group === group);
            if (items.length === 0) return null;
            return (
              <div key={group} className="mb-3">
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1.5">{GROUP_LABELS[group]}</p>
                <div className="grid grid-cols-2 gap-2">
                  {items.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setModel(m.id)}
                      className={`text-left px-3 py-2 rounded-lg border text-sm transition-colors ${
                        isSelected(m.id)
                          ? 'border-purple-500 bg-purple-500/10 text-white'
                          : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                      }`}
                    >
                      <span className="block font-medium truncate text-xs">{m.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Generation params */}
        <div className="space-y-5">
          <Slider
            label="Температура"
            tooltip={"Контролирует случайность ответов.\n\n0.0 — строго предсказуемый текст, модель всегда выбирает самое вероятное слово.\n0.3–0.5 — сдержанный стиль, мало неожиданностей.\n0.7 — баланс между точностью и творчеством (по умолчанию).\n1.0+ — более творческие, непредсказуемые ответы.\n2.0 — максимальная случайность, текст может стать бессвязным.\n\nПо умолчанию: 0.7"}
            value={local.temperature}
            onChange={(v) => update('temperature', v)}
            min={0}
            max={2}
            step={0.01}
          />
          <Slider
            label="Top-P"
            tooltip={"Ограничивает выбор слов по суммарной вероятности (nucleus sampling).\n\nМодель рассматривает только самые вероятные слова, пока их суммарная вероятность не достигнет этого порога.\n\n0.5 — только топ-50% вероятных слов, текст сдержаннее.\n0.9 — широкий выбор, текст разнообразнее.\n1.0 — все слова доступны.\n\nРаботает вместе с температурой. Обычно достаточно менять что-то одно.\n\nПо умолчанию: 0.95"}
            value={local.top_p}
            onChange={(v) => update('top_p', v)}
            min={0}
            max={1}
            step={0.01}
          />
          <Slider
            label="Top-K"
            tooltip={"Ограничивает выбор слов количеством: модель выбирает только из K самых вероятных вариантов.\n\n0 — отключено, модель выбирает из всех слов.\n10 — только топ-10 слов, текст очень предсказуемый.\n40–50 — хороший баланс.\n100 — почти без ограничений.\n\nПо умолчанию: 0 (отключено)"}
            value={local.top_k}
            onChange={(v) => update('top_k', Math.round(v))}
            min={0}
            max={100}
            step={1}
          />
          <Slider
            label="Штраф за повторения"
            tooltip={"Снижает вероятность повторения одних и тех же слов и фраз (frequency penalty).\n\n0.0 — без штрафа, модель может повторяться.\n0.3–0.5 — лёгкий штраф, убирает навязчивые повторы.\n1.0 — заметный штраф, текст более разнообразный.\n2.0 — сильный штраф, модель избегает любых повторов (может ухудшить связность).\n\nПо умолчанию: 0"}
            value={local.frequency_penalty}
            onChange={(v) => update('frequency_penalty', v)}
            min={0}
            max={2}
            step={0.01}
          />
          <Slider
            label="Макс. токенов"
            tooltip={"Максимальная длина ответа. 1 токен — примерно 3-4 символа или 1 слог на русском.\n\n256 — очень короткий ответ (~750 символов).\n1024 — короткий ответ (~3000 символов).\n2048 — средний ответ (~6000 символов).\n4096 — длинный ответ (~12000 символов).\n\nЭто жёсткий лимит: ответ обрежется, если превысит. Реальная длина зависит от настройки «Длина ответа» на персонаже.\n\nПо умолчанию: 2048"}
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
