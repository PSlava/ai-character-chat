import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { X, ChevronRight, Check, AlertTriangle } from 'lucide-react';
import type { GenerationSettings } from '@/hooks/useChat';
import type { OpenRouterModel } from '@/api/characters';

export interface ChatSettings extends GenerationSettings {
  model?: string;
}

interface Props {
  currentModel: string;
  orModels?: OpenRouterModel[];
  groqModels?: OpenRouterModel[];
  cerebrasModels?: OpenRouterModel[];
  togetherModels?: OpenRouterModel[];
  contentRating?: string;
  isAdmin?: boolean;
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
        className="w-full accent-rose-500"
      />
    </div>
  );
}

const GEN_DEFAULTS = {
  temperature: 0.8,
  top_p: 0.95,
  top_k: 0,
  frequency_penalty: 0.3,
  presence_penalty: 0.3,
  max_tokens: 2048,
};

// Per-provider parameter limits
type ParamLimits = {
  temperature: { max: number };
  top_k: boolean;
  frequency_penalty: { max: number } | false;
  presence_penalty: { max: number } | false;
};

const PROVIDER_LIMITS: Record<string, ParamLimits> = {
  default:    { temperature: { max: 2 }, top_k: false, frequency_penalty: { max: 1 }, presence_penalty: { max: 1 } },
  groq:       { temperature: { max: 2 }, top_k: false, frequency_penalty: { max: 1 }, presence_penalty: { max: 1 } },
  cerebras:   { temperature: { max: 1.5 }, top_k: false, frequency_penalty: false, presence_penalty: false },
  together:   { temperature: { max: 2 }, top_k: false, frequency_penalty: { max: 1 }, presence_penalty: { max: 1 } },
  openrouter: { temperature: { max: 2 }, top_k: true,  frequency_penalty: { max: 1 }, presence_penalty: { max: 1 } },
  deepseek:   { temperature: { max: 2 }, top_k: false, frequency_penalty: { max: 1 }, presence_penalty: { max: 1 } },
  qwen:       { temperature: { max: 2 }, top_k: false, frequency_penalty: { max: 1 }, presence_penalty: { max: 1 } },
  openai:     { temperature: { max: 2 }, top_k: false, frequency_penalty: { max: 2 }, presence_penalty: { max: 2 } },
  gemini:     { temperature: { max: 2 }, top_k: false, frequency_penalty: false, presence_penalty: false },
  claude:     { temperature: { max: 1 }, top_k: false, frequency_penalty: false, presence_penalty: false },
  grok:       { temperature: { max: 2 }, top_k: false, frequency_penalty: false, presence_penalty: false },
  mistral:    { temperature: { max: 1.5 }, top_k: false, frequency_penalty: false, presence_penalty: false },
};

function getProvider(modelId: string): string {
  if (modelId === 'auto') return 'default';
  if (modelId.startsWith('groq:') || modelId === 'groq') return 'groq';
  if (modelId.startsWith('cerebras:') || modelId === 'cerebras') return 'cerebras';
  if (modelId.startsWith('together:') || modelId === 'together') return 'together';
  if (modelId.includes('/')) return 'openrouter';
  if (modelId === 'openrouter') return 'openrouter';
  if (modelId === 'haiku') return 'claude';
  if (['deepseek', 'qwen', 'openai', 'gemini', 'claude', 'grok', 'mistral'].includes(modelId)) return modelId;
  return 'default';
}

function getLimits(modelId: string): ParamLimits {
  return PROVIDER_LIMITS[getProvider(modelId)] || PROVIDER_LIMITS.default;
}

function clampToLimits(settings: typeof GEN_DEFAULTS, modelId: string): typeof GEN_DEFAULTS {
  const limits = getLimits(modelId);
  const s = { ...settings };
  s.temperature = Math.min(s.temperature, limits.temperature.max);
  if (limits.frequency_penalty === false) s.frequency_penalty = 0;
  else s.frequency_penalty = Math.min(s.frequency_penalty, limits.frequency_penalty.max);
  if (limits.presence_penalty === false) s.presence_penalty = 0;
  else s.presence_penalty = Math.min(s.presence_penalty, limits.presence_penalty.max);
  if (!limits.top_k) s.top_k = 0;
  return s;
}

export function loadModelSettings(modelId: string): typeof GEN_DEFAULTS {
  try {
    const raw = localStorage.getItem(`model-settings:${modelId}`);
    if (raw) return clampToLimits({ ...GEN_DEFAULTS, ...JSON.parse(raw) }, modelId);
  } catch {}
  return clampToLimits({ ...GEN_DEFAULTS }, modelId);
}

function saveModelSettings(modelId: string, s: typeof GEN_DEFAULTS) {
  try { localStorage.setItem(`model-settings:${modelId}`, JSON.stringify(s)); } catch {}
}

// User-facing model cards (visible to all users)
const USER_MODELS = [
  { id: 'auto', label: 'Auto', nsfwOk: true },
  { id: 'deepseek', label: 'DeepSeek V3.2', nsfwOk: true },
  { id: 'grok', label: 'Grok 4.1', nsfwOk: true },
  { id: 'mistral', label: 'Mistral Medium', nsfwOk: true },
  { id: 'gemini', label: 'Gemini 3 Flash', nsfwOk: true },
  { id: 'haiku', label: 'Claude Haiku', nsfwOk: false },
];

// Admin-only direct providers
const ADMIN_DIRECT_MODELS = [
  { id: 'claude', label: 'Claude Sonnet', nsfwOk: false },
  { id: 'openai', label: 'GPT-4o', nsfwOk: true },
  { id: 'qwen', label: 'Qwen', nsfwOk: false },
];

// Resolve description i18n key for a model ID
function descKey(id: string): string {
  return `settings.desc${id.charAt(0).toUpperCase()}${id.slice(1)}`;
}

export function GenerationSettingsModal({ currentModel, orModels = [], groqModels = [], cerebrasModels = [], togetherModels = [], contentRating, isAdmin, onApply, onClose }: Props) {
  const { t } = useTranslation();
  const [model, setModel] = useState(currentModel);
  const [local, setLocal] = useState(() => loadModelSettings(currentModel));
  const [showPicker, setShowPicker] = useState(false);
  const [pickerModel, setPickerModel] = useState(currentModel);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [advancedConfirmed, setAdvancedConfirmed] = useState(false);
  const [showAdvancedWarning, setShowAdvancedWarning] = useState(false);

  const update = <K extends keyof typeof GEN_DEFAULTS>(key: K, value: number) =>
    setLocal((prev) => ({ ...prev, [key]: value }));

  const isNsfw = contentRating === 'nsfw';

  // Resolve display info for any model ID
  const getModelInfo = (id: string): { label: string; desc?: string; nsfwOk: boolean } => {
    const userM = USER_MODELS.find((m) => m.id === id);
    if (userM) return { ...userM, desc: t(descKey(id) as any) };
    const adminM = ADMIN_DIRECT_MODELS.find((m) => m.id === id);
    if (adminM) return { ...adminM, desc: t(descKey(id) as any) };
    if (['groq', 'openrouter', 'cerebras', 'together'].includes(id))
      return { label: `${id.charAt(0).toUpperCase()}${id.slice(1)} Auto`, nsfwOk: true };
    if (id.startsWith('groq:')) {
      const found = groqModels.find((m) => m.id === id.slice(5));
      return { label: found ? `Groq: ${found.name}` : `Groq: ${id.slice(5)}`, nsfwOk: found?.nsfw !== false };
    }
    if (id.startsWith('cerebras:')) {
      const found = cerebrasModels.find((m) => m.id === id.slice(9));
      return { label: found ? `Cerebras: ${found.name}` : `Cerebras: ${id.slice(9)}`, nsfwOk: found?.nsfw !== false };
    }
    if (id.startsWith('together:')) {
      const found = togetherModels.find((m) => m.id === id.slice(9));
      return { label: found ? `Together: ${found.name}` : `Together: ${id.slice(9)}`, nsfwOk: found?.nsfw !== false };
    }
    if (id.includes('/')) {
      const found = orModels.find((m) => m.id === id);
      return { label: found ? found.name : id, nsfwOk: found?.nsfw !== false };
    }
    return { label: id, nsfwOk: true };
  };

  const selectModel = (id: string) => {
    setPickerModel(id);
  };

  const confirmPicker = () => {
    setModel(pickerModel);
    setLocal(clampToLimits(loadModelSettings(pickerModel), pickerModel));
    setShowPicker(false);
  };

  const openPicker = () => {
    setPickerModel(model);
    setShowPicker(true);
  };

  const handleAdvancedClick = () => {
    if (showAdvanced) {
      setShowAdvanced(false);
    } else if (advancedConfirmed) {
      setShowAdvanced(true);
    } else {
      setShowAdvancedWarning(true);
    }
  };

  const currentInfo = getModelInfo(model);
  const limits = getLimits(model);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-neutral-900 border border-neutral-700 rounded-2xl p-4 sm:p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {showPicker ? (
          /* ── Model picker view ── */
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold">{t('settings.chooseModel')}</h2>
            </div>

            {/* User models */}
            <div className="space-y-2">
              {USER_MODELS.map((m) => {
                const disabled = isNsfw && !m.nsfwOk;
                const selected = pickerModel === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => !disabled && selectModel(m.id)}
                    disabled={disabled}
                    className={`w-full text-left px-4 py-3 rounded-xl border transition-colors ${
                      disabled
                        ? 'border-neutral-800 bg-neutral-800/50 text-neutral-600 cursor-not-allowed'
                        : selected
                          ? 'border-rose-500 bg-rose-500/10 text-white'
                          : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                    }`}
                    title={disabled ? t('settings.nsfwBlocked') : undefined}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{m.label}</span>
                      {selected && <Check size={18} className="text-rose-400 shrink-0" />}
                    </div>
                    <span className="block text-xs text-neutral-500 mt-1 leading-relaxed">{t(descKey(m.id) as any)}</span>
                  </button>
                );
              })}
            </div>

            {/* Admin section */}
            {isAdmin && (
              <>
                <div className="mt-6 mb-3">
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">Admin</p>
                </div>

                {/* Direct providers */}
                <div className="space-y-2 mb-4">
                  {ADMIN_DIRECT_MODELS.map((m) => {
                    const disabled = isNsfw && !m.nsfwOk;
                    const selected = pickerModel === m.id;
                    return (
                      <button
                        key={m.id}
                        onClick={() => !disabled && selectModel(m.id)}
                        disabled={disabled}
                        className={`w-full text-left px-4 py-3 rounded-xl border transition-colors ${
                          disabled
                            ? 'border-neutral-800 bg-neutral-800/50 text-neutral-600 cursor-not-allowed'
                            : selected
                              ? 'border-rose-500 bg-rose-500/10 text-white'
                              : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                        }`}
                        title={disabled ? t('settings.nsfwBlocked') : undefined}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{m.label}</span>
                          {selected && <Check size={18} className="text-rose-400 shrink-0" />}
                        </div>
                        <span className="block text-xs text-neutral-500 mt-1 leading-relaxed">{t(descKey(m.id) as any)}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Aggregators with internal models */}
                {[
                  { key: 'groq', label: 'Groq', models: groqModels, prefix: 'groq:' },
                  { key: 'openrouter', label: 'OpenRouter', models: orModels, prefix: '' },
                  { key: 'cerebras', label: 'Cerebras', models: cerebrasModels, prefix: 'cerebras:' },
                  { key: 'together', label: 'Together', models: togetherModels, prefix: 'together:' },
                ].map(({ key, label, models, prefix }) => (
                  <div key={key} className="mb-4">
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">{label}</p>
                    <div className="space-y-1.5">
                      <button
                        onClick={() => selectModel(key)}
                        className={`w-full text-left px-3 py-2 rounded-lg border text-sm transition-colors ${
                          pickerModel === key
                            ? 'border-rose-500 bg-rose-500/10 text-white'
                            : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-xs">{label} Auto</span>
                          {pickerModel === key && <Check size={14} className="text-rose-400 shrink-0" />}
                        </div>
                      </button>
                      {models.map((m) => {
                        const fullId = prefix ? `${prefix}${m.id}` : m.id;
                        const disabled = isNsfw && m.nsfw === false;
                        const selected = pickerModel === fullId;
                        return (
                          <button
                            key={fullId}
                            onClick={() => !disabled && selectModel(fullId)}
                            disabled={disabled}
                            className={`w-full text-left px-3 py-2 rounded-lg border text-sm transition-colors ${
                              disabled
                                ? 'border-neutral-800 bg-neutral-800/50 text-neutral-600 cursor-not-allowed'
                                : selected
                                  ? 'border-rose-500 bg-rose-500/10 text-white'
                                  : 'border-neutral-700 bg-neutral-800 text-neutral-300 hover:border-neutral-500'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-xs">{m.name} ({m.quality}/10)</span>
                              {selected && <Check size={14} className="text-rose-400 shrink-0" />}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* OK / Cancel */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowPicker(false)}
                className="flex-1 px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={confirmPicker}
                className="flex-1 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                OK
              </button>
            </div>
          </>
        ) : (
          /* ── Default view ── */
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold">{t('settings.title')}</h2>
              <button onClick={onClose} className="p-1 text-neutral-400 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>

            {/* Current model card */}
            <div className="mb-6">
              <p className="text-sm text-neutral-400 mb-3">{t('settings.modelLabel')}</p>
              <div className="border border-neutral-700 rounded-xl p-4 bg-neutral-800/50">
                <h3 className="text-base font-semibold text-white">{currentInfo.label}</h3>
                {currentInfo.desc && (
                  <p className="text-sm text-neutral-400 mt-1 leading-relaxed">{currentInfo.desc}</p>
                )}
                <button
                  onClick={openPicker}
                  className="mt-3 w-full px-4 py-2 border border-neutral-600 rounded-lg text-sm text-neutral-300 hover:border-neutral-400 hover:text-white transition-colors"
                >
                  {t('settings.changeModel')}
                </button>
              </div>
            </div>

            {/* Advanced settings toggle */}
            <div className="mb-4">
              <button
                onClick={handleAdvancedClick}
                className="w-full flex items-center justify-between px-4 py-3 border border-neutral-700 rounded-xl text-sm text-neutral-300 hover:border-neutral-500 hover:text-white transition-colors"
              >
                <span>{showAdvanced ? t('settings.advancedHide') : t('settings.advancedSettings')}</span>
                <ChevronRight size={16} className={`transition-transform ${showAdvanced ? 'rotate-90' : ''}`} />
              </button>
            </div>

            {/* Advanced settings content */}
            {showAdvanced && (
              <div className="space-y-5 mb-4 px-1">
                <Slider
                  label={t('settings.temperature')}
                  tooltip={t('settings.temperatureTooltip')}
                  value={local.temperature}
                  onChange={(v) => update('temperature', Math.min(v, limits.temperature.max))}
                  min={0}
                  max={limits.temperature.max}
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
                {limits.top_k && (
                  <Slider
                    label={t('settings.topK')}
                    tooltip={t('settings.topKTooltip')}
                    value={local.top_k}
                    onChange={(v) => update('top_k', Math.round(v))}
                    min={0}
                    max={100}
                    step={1}
                  />
                )}
                {limits.frequency_penalty !== false ? (
                  <Slider
                    label={t('settings.frequencyPenalty')}
                    tooltip={t('settings.frequencyPenaltyTooltip')}
                    value={local.frequency_penalty}
                    onChange={(v) => update('frequency_penalty', Math.min(v, (limits.frequency_penalty as { max: number }).max))}
                    min={0}
                    max={(limits.frequency_penalty as { max: number }).max}
                    step={0.01}
                  />
                ) : (
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm text-neutral-500">{t('settings.frequencyPenalty')}</span>
                    <span className="text-xs text-neutral-600">&mdash; {t('settings.notSupported')}</span>
                  </div>
                )}
                {limits.presence_penalty !== false ? (
                  <Slider
                    label={t('settings.presencePenalty')}
                    tooltip={t('settings.presencePenaltyTooltip')}
                    value={local.presence_penalty}
                    onChange={(v) => update('presence_penalty', Math.min(v, (limits.presence_penalty as { max: number }).max))}
                    min={0}
                    max={(limits.presence_penalty as { max: number }).max}
                    step={0.01}
                  />
                ) : (
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm text-neutral-500">{t('settings.presencePenalty')}</span>
                    <span className="text-xs text-neutral-600">&mdash; {t('settings.notSupported')}</span>
                  </div>
                )}
                <Slider
                  label={t('settings.maxTokens')}
                  tooltip={t('settings.maxTokensTooltip')}
                  value={local.max_tokens}
                  onChange={(v) => update('max_tokens', Math.round(v))}
                  min={256}
                  max={4096}
                  step={128}
                />
                <button
                  onClick={() => setLocal(clampToLimits({ ...GEN_DEFAULTS }, model))}
                  className="w-full px-4 py-2 border border-neutral-700 rounded-lg text-sm text-neutral-400 hover:text-white hover:border-neutral-500 transition-colors"
                >
                  {t('settings.resetDefaults')}
                </button>
              </div>
            )}

            {/* Cancel / Apply */}
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => { saveModelSettings(model, local); onApply({ ...local, model }); onClose(); }}
                className="flex-1 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {t('common.apply')}
              </button>
            </div>
          </>
        )}

        {/* Advanced warning dialog */}
        {showAdvancedWarning && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50" onClick={() => setShowAdvancedWarning(false)}>
            <div
              className="bg-neutral-900 border border-neutral-600 rounded-2xl p-5 sm:p-6 w-full max-w-sm mx-4 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-amber-500/10 rounded-lg">
                  <AlertTriangle size={20} className="text-amber-400" />
                </div>
                <h3 className="text-base font-semibold text-white">{t('settings.advancedWarningTitle')}</h3>
              </div>
              <p className="text-sm text-neutral-400 mb-5 leading-relaxed">{t('settings.advancedWarningText')}</p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowAdvancedWarning(false)}
                  className="flex-1 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={() => { setAdvancedConfirmed(true); setShowAdvancedWarning(false); setShowAdvanced(true); }}
                  className="flex-1 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {t('settings.advancedContinue')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
