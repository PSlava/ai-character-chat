import { useState, useEffect } from 'react';
import { Input, Textarea } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { getOpenRouterModels } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import type { Character } from '@/types';

interface Props {
  initial?: Partial<Character>;
  onSubmit: (data: Partial<Character>) => Promise<void>;
  submitLabel?: string;
}

// AI may return arrays instead of strings — normalize to string
const str = (v: unknown): string =>
  Array.isArray(v) ? v.join('\n') : typeof v === 'string' ? v : '';

export function CharacterForm({ initial, onSubmit, submitLabel = 'Создать' }: Props) {
  const [form, setForm] = useState({
    name: str(initial?.name),
    tagline: str(initial?.tagline),
    personality: str(initial?.personality),
    scenario: str(initial?.scenario),
    greeting_message: str(initial?.greeting_message),
    example_dialogues: str(initial?.example_dialogues),
    content_rating: initial?.content_rating || 'sfw',
    system_prompt_suffix: str(initial?.system_prompt_suffix),
    tags: Array.isArray(initial?.tags) ? initial.tags.join(', ') : '',
    is_public: initial?.is_public ?? true,
    preferred_model: initial?.preferred_model || 'qwen',
    max_tokens: initial?.max_tokens ?? 2048,
    response_length: initial?.response_length || 'long',
  });
  const [loading, setLoading] = useState(false);
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);

  useEffect(() => {
    getOpenRouterModels().then(setOrModels).catch(() => {});
  }, []);

  const update = (field: string, value: string | boolean | number) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        name: form.name,
        tagline: form.tagline || undefined,
        personality: form.personality,
        scenario: form.scenario || undefined,
        greeting_message: form.greeting_message,
        example_dialogues: form.example_dialogues || undefined,
        content_rating: form.content_rating as Character['content_rating'],
        system_prompt_suffix: form.system_prompt_suffix || undefined,
        tags: form.tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
        is_public: form.is_public,
        preferred_model: form.preferred_model,
        max_tokens: form.max_tokens,
        response_length: form.response_length as Character['response_length'],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <Input
        label="Имя персонажа *"
        value={form.name}
        onChange={(e) => update('name', e.target.value)}
        placeholder="Например: Шерлок Холмс"
        required
      />

      <Input
        label="Краткое описание"
        value={form.tagline}
        onChange={(e) => update('tagline', e.target.value)}
        placeholder="Гениальный детектив с Бейкер-стрит"
      />

      <Textarea
        label="Личность и характер *"
        value={form.personality}
        onChange={(e) => update('personality', e.target.value)}
        placeholder="Опишите характер, манеру речи, привычки..."
        rows={4}
        required
      />

      <Textarea
        label="Сценарий / Мир"
        value={form.scenario}
        onChange={(e) => update('scenario', e.target.value)}
        placeholder="Описание ситуации, мира, контекста взаимодействия..."
        rows={3}
      />

      <Textarea
        label="Приветственное сообщение *"
        value={form.greeting_message}
        onChange={(e) => update('greeting_message', e.target.value)}
        placeholder="Первое сообщение персонажа при начале чата"
        rows={3}
        required
      />

      <Textarea
        label="Примеры диалогов"
        value={form.example_dialogues}
        onChange={(e) => update('example_dialogues', e.target.value)}
        placeholder="User: Привет!\nCharacter: *поправляет скрипку* Здравствуйте. Чем могу быть полезен?"
        rows={4}
      />

      <Textarea
        label="Дополнительные инструкции"
        value={form.system_prompt_suffix}
        onChange={(e) => update('system_prompt_suffix', e.target.value)}
        placeholder="Дополнительные правила для AI..."
        rows={2}
      />

      <Input
        label="Теги (через запятую)"
        value={form.tags}
        onChange={(e) => update('tags', e.target.value)}
        placeholder="детектив, классика, Англия"
      />

      <div className="flex gap-4 flex-wrap">
        <div>
          <label className="block text-sm text-neutral-400 mb-1">
            Рейтинг контента
          </label>
          <select
            value={form.content_rating}
            onChange={(e) => update('content_rating', e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white"
          >
            <option value="sfw">SFW</option>
            <option value="moderate">Moderate</option>
            <option value="nsfw">NSFW</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-neutral-400 mb-1">
            Длина ответа
          </label>
          <select
            value={form.response_length}
            onChange={(e) => update('response_length', e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white"
          >
            <option value="short">Короткий (1-3 предложения)</option>
            <option value="medium">Средний (1-2 абзаца)</option>
            <option value="long">Длинный (2-4 абзаца)</option>
            <option value="very_long">Очень длинный (4-6 абзацев)</option>
          </select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm text-neutral-400 mb-1">
            AI Модель (для чата)
          </label>
          <select
            value={form.preferred_model}
            onChange={(e) => update('preferred_model', e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white w-full"
          >
            <option value="openrouter">OpenRouter Auto (Free)</option>
            {orModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.quality}/10)
              </option>
            ))}
            <option disabled>───────────</option>
            <option value="groq">Groq (Qwen 32B)</option>
            <option value="cerebras">Cerebras (Qwen 32B)</option>
            <option value="deepseek">DeepSeek</option>
            <option value="qwen">Qwen (DashScope)</option>
            <option disabled>───────────</option>
            <option value="gemini">Gemini</option>
            <option value="claude">Claude</option>
            <option value="openai">GPT-4o</option>
          </select>
        </div>

        <div className="flex items-end">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_public}
              onChange={(e) => update('is_public', e.target.checked)}
              className="w-4 h-4 rounded accent-purple-600"
            />
            <span className="text-sm text-neutral-300">Публичный</span>
          </label>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-sm text-neutral-400">
            Макс. токенов ответа
          </label>
          <span className="text-sm text-neutral-300">{form.max_tokens}</span>
        </div>
        <input
          type="range"
          value={form.max_tokens}
          onChange={(e) => update('max_tokens', Number(e.target.value))}
          min={256}
          max={4096}
          step={128}
          className="w-full accent-purple-500"
        />
        <p className="text-xs text-neutral-500 mt-1">
          Максимальная длина ответа. 1 токен ≈ 3-4 символа. По умолчанию: 2048.
        </p>
      </div>

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? 'Сохранение...' : submitLabel}
      </Button>
    </form>
  );
}
