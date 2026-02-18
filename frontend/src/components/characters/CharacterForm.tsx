import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import { Input, Textarea } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AvatarUpload } from '@/components/ui/AvatarUpload';
import { getOpenRouterModels, getGroqModels, getCerebrasModels, getTogetherModels, getStructuredTags } from '@/api/characters';
import type { OpenRouterModel, StructuredTagsResponse } from '@/api/characters';
import type { Character } from '@/types';

interface Props {
  initial?: Partial<Character>;
  onSubmit: (data: Partial<Character>) => Promise<void>;
  submitLabel?: string;
  isAdmin?: boolean;
}

// AI may return arrays instead of strings — normalize to string
const str = (v: unknown): string =>
  Array.isArray(v) ? v.join('\n') : typeof v === 'string' ? v : '';

export function CharacterForm({ initial, onSubmit, submitLabel, isAdmin }: Props) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const [form, setForm] = useState({
    avatar_url: initial?.avatar_url || '',
    name: str(initial?.name),
    tagline: str(initial?.tagline),
    personality: str(initial?.personality),
    appearance: str(initial?.appearance),
    scenario: str(initial?.scenario),
    greeting_message: str(initial?.greeting_message),
    example_dialogues: str(initial?.example_dialogues),
    content_rating: initial?.content_rating || 'sfw',
    system_prompt_suffix: str(initial?.system_prompt_suffix),
    tags: Array.isArray(initial?.tags) ? initial.tags.join(', ') : '',
    structured_tags: initial?.structured_tags || [] as string[],
    is_public: initial?.is_public ?? true,
    preferred_model: (!isAdmin && ['gemini', 'claude', 'openai'].includes(initial?.preferred_model || ''))
      ? 'auto'
      : (initial?.preferred_model || 'qwen'),
    max_tokens: initial?.max_tokens ?? 2048,
    response_length: initial?.response_length || 'long',
  });
  const [loading, setLoading] = useState(false);
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);
  const [groqModels, setGroqModels] = useState<OpenRouterModel[]>([]);
  const [cerebrasModels, setCerebrasModels] = useState<OpenRouterModel[]>([]);
  const [togetherModels, setTogetherModels] = useState<OpenRouterModel[]>([]);
  const [tagRegistry, setTagRegistry] = useState<StructuredTagsResponse | null>(null);

  useEffect(() => {
    getOpenRouterModels().then(setOrModels).catch(() => {});
    getGroqModels().then(setGroqModels).catch(() => {});
    getCerebrasModels().then(setCerebrasModels).catch(() => {});
    getTogetherModels().then(setTogetherModels).catch(() => {});
    getStructuredTags().then(setTagRegistry).catch(() => {});
  }, []);

  const update = (field: string, value: string | boolean | number) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const toggleTag = (tagId: string) =>
    setForm((prev) => ({
      ...prev,
      structured_tags: prev.structured_tags.includes(tagId)
        ? prev.structured_tags.filter((t) => t !== tagId)
        : [...prev.structured_tags, tagId],
    }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.is_public && !form.avatar_url) {
      toast.error(t('form.avatarRequiredError'));
      return;
    }
    setLoading(true);
    try {
      await onSubmit({
        avatar_url: form.avatar_url || undefined,
        name: form.name,
        tagline: form.tagline || undefined,
        personality: form.personality,
        appearance: form.appearance || undefined,
        scenario: form.scenario || undefined,
        greeting_message: form.greeting_message,
        example_dialogues: form.example_dialogues || undefined,
        content_rating: form.content_rating as Character['content_rating'],
        system_prompt_suffix: form.system_prompt_suffix || undefined,
        tags: form.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
        structured_tags: form.structured_tags,
        is_public: form.is_public,
        preferred_model: form.preferred_model,
        max_tokens: form.max_tokens,
        response_length: form.response_length as Character['response_length'],
        original_language: i18n.language,
      } as Partial<Character>);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <AvatarUpload
        currentUrl={form.avatar_url || null}
        name={form.name || '?'}
        onChange={(url) => setForm((prev) => ({ ...prev, avatar_url: url }))}
        required={form.is_public}
        isAdmin={isAdmin}
        characterDescription={form.appearance || form.personality || ''}
      />

      <Input
        label={t('form.name')}
        value={form.name}
        onChange={(e) => update('name', e.target.value)}
        placeholder={t('form.namePlaceholder')}
        maxLength={100}
        required
      />

      <Input
        label={t('form.tagline')}
        value={form.tagline}
        onChange={(e) => update('tagline', e.target.value)}
        placeholder={t('form.taglinePlaceholder')}
        maxLength={300}
      />

      <Textarea
        label={t('form.personality')}
        value={form.personality}
        onChange={(e) => update('personality', e.target.value)}
        placeholder={t('form.personalityPlaceholder')}
        rows={4}
        maxLength={10000}
        required
      />

      {tagRegistry && tagRegistry.categories.length > 0 && (
        <div>
          <label className="block text-sm text-neutral-400 mb-1">
            {t('form.structuredTags')}
          </label>
          <p className="text-xs text-neutral-500 mb-3">{t('form.structuredTagsHint')}</p>
          {tagRegistry.categories.map((cat) => (
            <div key={cat.id} className="mb-3">
              <div className="text-xs text-neutral-500 mb-1.5 uppercase tracking-wider">
                {lang === 'ru' ? cat.label_ru : cat.label_en}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {tagRegistry.tags[cat.id]?.map((tag) => {
                  const selected = form.structured_tags.includes(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => toggleTag(tag.id)}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        selected
                          ? 'bg-rose-600 text-white'
                          : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700 hover:text-neutral-200'
                      }`}
                    >
                      {lang === 'ru' ? tag.label_ru : tag.label_en}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      <Textarea
        label={t('form.appearance')}
        value={form.appearance}
        onChange={(e) => update('appearance', e.target.value)}
        placeholder={t('form.appearancePlaceholder')}
        rows={3}
        maxLength={5000}
      />

      <Textarea
        label={t('form.scenario')}
        value={form.scenario}
        onChange={(e) => update('scenario', e.target.value)}
        placeholder={t('form.scenarioPlaceholder')}
        rows={3}
        maxLength={5000}
      />

      <Textarea
        label={t('form.greeting')}
        value={form.greeting_message}
        onChange={(e) => update('greeting_message', e.target.value)}
        placeholder={t('form.greetingPlaceholder')}
        rows={3}
        maxLength={5000}
        required
      />

      <Textarea
        label={t('form.exampleDialogues')}
        value={form.example_dialogues}
        onChange={(e) => update('example_dialogues', e.target.value)}
        placeholder={t('form.exampleDialoguesPlaceholder')}
        rows={4}
        maxLength={10000}
      />

      {isAdmin && (
      <Textarea
        label={t('form.instructions')}
        value={form.system_prompt_suffix}
        onChange={(e) => update('system_prompt_suffix', e.target.value)}
        placeholder={t('form.instructionsPlaceholder')}
        rows={2}
        maxLength={5000}
      />
      )}

      <Input
        label={t('form.tags')}
        value={form.tags}
        onChange={(e) => update('tags', e.target.value)}
        placeholder={t('form.tagsPlaceholder')}
        maxLength={500}
      />

      <div className="flex gap-4 flex-wrap">
        <div>
          <label className="block text-sm text-neutral-400 mb-1">
            {t('form.contentRating')}
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

        {isAdmin && (
        <div>
          <label className="block text-sm text-neutral-400 mb-1">
            {t('form.responseLength')}
          </label>
          <select
            value={form.response_length}
            onChange={(e) => update('response_length', e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white"
          >
            <option value="short">{t('form.lengthShort')}</option>
            <option value="medium">{t('form.lengthMedium')}</option>
            <option value="long">{t('form.lengthLong')}</option>
            <option value="very_long">{t('form.lengthVeryLong')}</option>
          </select>
        </div>
        )}

        {isAdmin && (
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm text-neutral-400 mb-1">
            {t('form.preferredModel')}
          </label>
          <select
            value={form.preferred_model}
            onChange={(e) => update('preferred_model', e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white w-full"
          >
            <option value="auto">{t('form.autoAll')}</option>
            <option value="openrouter">{t('form.openrouterAuto')}</option>
            {orModels.map((m) => (
              <option key={m.id} value={m.id} disabled={form.content_rating === 'nsfw' && m.nsfw === false}>
                {m.name} ({m.quality}/10)
              </option>
            ))}
            <option disabled>{t('form.groqSeparator')}</option>
            <option value="groq">{t('form.groqAuto')}</option>
            {groqModels.map((m) => (
              <option key={`groq:${m.id}`} value={`groq:${m.id}`} disabled={form.content_rating === 'nsfw' && m.nsfw === false}>
                {m.name} ({m.quality}/10)
              </option>
            ))}
            <option disabled>{t('form.cerebrasSeparator')}</option>
            <option value="cerebras">{t('form.cerebrasAuto')}</option>
            {cerebrasModels.map((m) => (
              <option key={`cerebras:${m.id}`} value={`cerebras:${m.id}`} disabled={form.content_rating === 'nsfw' && m.nsfw === false}>
                {m.name} ({m.quality}/10)
              </option>
            ))}
            <option disabled>{t('form.togetherSeparator')}</option>
            <option value="together">{t('form.togetherAuto')}</option>
            {togetherModels.map((m) => (
              <option key={`together:${m.id}`} value={`together:${m.id}`} disabled={form.content_rating === 'nsfw' && m.nsfw === false}>
                {m.name} ({m.quality}/10)
              </option>
            ))}
            <option disabled>{t('form.directApiSeparator')}</option>
            <option value="deepseek">DeepSeek</option>
            <option value="qwen" disabled={form.content_rating === 'nsfw'}>Qwen (DashScope)</option>
            <option disabled>{t('form.paidSeparator')}</option>
            <option value="gemini">Gemini</option>
            <option value="claude">Claude</option>
            <option value="openai">GPT-4o</option>
          </select>
        </div>
        )}

        <div className="flex items-end">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_public}
              onChange={(e) => update('is_public', e.target.checked)}
              className="w-4 h-4 rounded accent-rose-600"
            />
            <span className="text-sm text-neutral-300">{t('form.public')}</span>
          </label>
        </div>
      </div>

      {isAdmin && (
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-sm text-neutral-400">
            {t('form.maxTokens')}
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
          className="w-full accent-rose-500"
        />
        <p className="text-xs text-neutral-500 mt-1">
          {t('form.maxTokensHelp')}
        </p>
      </div>
      )}

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? t('common.saving') : (submitLabel || t('common.create'))}
      </Button>
    </form>
  );
}
