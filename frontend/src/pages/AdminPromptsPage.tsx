import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate } from 'react-router-dom';
import { ChevronDown, ChevronRight, RotateCcw, Save } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { getPrompts, updatePrompt, resetPrompt } from '@/api/admin';
import type { PromptEntry } from '@/api/admin';

const KEY_LABELS: Record<string, Record<string, string>> = {
  ru: {
    intro: 'Вступление',
    personality: 'Заголовок: Личность',
    scenario: 'Заголовок: Сценарий',
    examples: 'Заголовок: Примеры',
    content_rules_header: 'Заголовок: Правила контента',
    content_sfw: 'Контент: SFW',
    content_moderate: 'Контент: Moderate',
    content_nsfw: 'Контент: NSFW',
    extra_instructions: 'Заголовок: Доп. инструкции',
    user_section: 'Заголовок: Пользователь',
    user_name_line: 'Имя пользователя',
    format_header: 'Заголовок: Формат',
    rules_header: 'Заголовок: Правила',
    length_short: 'Длина: Короткий',
    length_medium: 'Длина: Средний',
    length_long: 'Длина: Длинный',
    length_very_long: 'Длина: Очень длинный',
    format_rules: 'Правила формата',
    rules: 'Основные правила',
  },
  en: {
    intro: 'Introduction',
    personality: 'Header: Personality',
    scenario: 'Header: Scenario',
    examples: 'Header: Examples',
    content_rules_header: 'Header: Content Rules',
    content_sfw: 'Content: SFW',
    content_moderate: 'Content: Moderate',
    content_nsfw: 'Content: NSFW',
    extra_instructions: 'Header: Extra Instructions',
    user_section: 'Header: User',
    user_name_line: 'User Name Line',
    format_header: 'Header: Format',
    rules_header: 'Header: Rules',
    length_short: 'Length: Short',
    length_medium: 'Length: Medium',
    length_long: 'Length: Long',
    length_very_long: 'Length: Very Long',
    format_rules: 'Format Rules',
    rules: 'Main Rules',
  },
};

function getLabel(fullKey: string): string {
  const [lang, ...rest] = fullKey.split('.');
  const key = rest.join('.');
  return KEY_LABELS[lang]?.[key] || KEY_LABELS.en?.[key] || key;
}

interface PromptCardProps {
  entry: PromptEntry;
  onSave: (key: string, value: string) => Promise<void>;
  onReset: (key: string) => Promise<void>;
  t: (key: string) => string;
}

function PromptCard({ entry, onSave, onReset, t }: PromptCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [text, setText] = useState(entry.override ?? entry.default);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const isOverridden = entry.override !== null;
  const currentValue = entry.override ?? entry.default;
  const hasChanges = text !== currentValue;

  useEffect(() => {
    setText(entry.override ?? entry.default);
  }, [entry.override, entry.default]);

  const handleSave = async () => {
    setSaving(true);
    await onSave(entry.key, text);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = async () => {
    if (!confirm(t('admin.resetConfirm'))) return;
    await onReset(entry.key);
    setText(entry.default);
  };

  return (
    <div className="border border-neutral-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-4 py-3 text-left hover:bg-neutral-800/50 transition-colors"
      >
        {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <span className="flex-1 font-medium text-sm">{getLabel(entry.key)}</span>
        <span className="text-[10px] text-neutral-600 font-mono">{entry.key}</span>
        {isOverridden ? (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-600/20 text-purple-400">
            {t('admin.overridden')}
          </span>
        ) : (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-500">
            {t('admin.default')}
          </span>
        )}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={Math.min(Math.max(text.split('\n').length + 1, 3), 12)}
            className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white font-mono resize-y focus:outline-none focus:border-purple-500"
          />
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={!hasChanges || saving}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-40"
            >
              <Save size={13} />
              {saving ? t('common.saving') : t('common.save')}
            </button>
            {isOverridden && (
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
              >
                <RotateCcw size={13} />
                {t('admin.reset')}
              </button>
            )}
            {saved && (
              <span className="text-xs text-green-400">{t('common.saved')}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function AdminPromptsPage() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const [prompts, setPrompts] = useState<PromptEntry[]>([]);
  const [loadingPrompts, setLoadingPrompts] = useState(true);
  const [tab, setTab] = useState<'ru' | 'en'>('ru');

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) return;
    getPrompts()
      .then(setPrompts)
      .finally(() => setLoadingPrompts(false));
  }, [isAdmin]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-neutral-500">{t('common.loading')}</div>
      </div>
    );
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  const filtered = prompts.filter((p) => p.key.startsWith(`${tab}.`));

  const handleSave = async (key: string, value: string) => {
    await updatePrompt(key, value);
    setPrompts((prev) =>
      prev.map((p) => (p.key === key ? { ...p, override: value } : p))
    );
  };

  const handleReset = async (key: string) => {
    await resetPrompt(key);
    setPrompts((prev) =>
      prev.map((p) => (p.key === key ? { ...p, override: null } : p))
    );
  };

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">{t('admin.promptsTitle')}</h1>
        <p className="text-neutral-400 mt-1 text-sm">{t('admin.promptsSubtitle')}</p>
      </div>

      <div className="flex gap-2 mb-6">
        {(['ru', 'en'] as const).map((lang) => (
          <button
            key={lang}
            onClick={() => setTab(lang)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === lang
                ? 'bg-purple-600 text-white'
                : 'bg-neutral-800 text-neutral-400 hover:text-white'
            }`}
          >
            {lang.toUpperCase()}
          </button>
        ))}
      </div>

      {loadingPrompts ? (
        <div className="text-neutral-500 text-sm">{t('common.loading')}</div>
      ) : (
        <div className="space-y-2">
          {filtered.map((entry) => (
            <PromptCard
              key={entry.key}
              entry={entry}
              onSave={handleSave}
              onReset={handleReset}
              t={t}
            />
          ))}
        </div>
      )}
    </div>
  );
}
