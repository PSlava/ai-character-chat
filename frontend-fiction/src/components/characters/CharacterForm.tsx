import { useState, useEffect, useMemo } from 'react';
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
    speech_pattern: str(initial?.speech_pattern),
    backstory: str(initial?.backstory),
    hidden_layers: str(initial?.hidden_layers),
    inner_conflict: str(initial?.inner_conflict),
    companion_name: str(initial?.companion_name),
    companion_role: initial?.companion_role || '',
    companion_personality: str(initial?.companion_personality),
    companion_appearance: str(initial?.companion_appearance),
    companion_speech_pattern: str(initial?.companion_speech_pattern),
    companion_backstory: str(initial?.companion_backstory),
    companion_avatar_url: initial?.companion_avatar_url || '',
    scenario: str(initial?.scenario),
    greeting_message: str(initial?.greeting_message),
    example_dialogues: str(initial?.example_dialogues),
    content_rating: initial?.content_rating || 'sfw',
    system_prompt_suffix: str(initial?.system_prompt_suffix),
    tags: Array.isArray(initial?.tags) ? initial.tags.join(', ') : '',
    structured_tags: initial?.structured_tags || [] as string[],
    is_public: initial?.is_public ?? true,
    preferred_model: (!isAdmin && ['gemini', 'openai'].includes(initial?.preferred_model || ''))
      ? 'auto'
      : (initial?.preferred_model || 'auto'),
    max_tokens: initial?.max_tokens ?? 2048,
    response_length: initial?.response_length || 'long',
  });
  const [companionEnabled, setCompanionEnabled] = useState(!!initial?.companion_name);
  const [loading, setLoading] = useState(false);
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);
  const [groqModels, setGroqModels] = useState<OpenRouterModel[]>([]);
  const [cerebrasModels, setCerebrasModels] = useState<OpenRouterModel[]>([]);
  const [togetherModels, setTogetherModels] = useState<OpenRouterModel[]>([]);
  const [tagRegistry, setTagRegistry] = useState<StructuredTagsResponse | null>(null);

  useEffect(() => {
    if (isAdmin) {
      getOpenRouterModels().then(setOrModels).catch(() => {});
      getGroqModels().then(setGroqModels).catch(() => {});
      getCerebrasModels().then(setCerebrasModels).catch(() => {});
      getTogetherModels().then(setTogetherModels).catch(() => {});
    }
    getStructuredTags().then(setTagRegistry).catch(() => {});
  }, []);

  const update = (field: string, value: string | boolean | number) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  // Approximate token count for system prompt (~4 chars/token for Latin, ~2 for Cyrillic/CJK)
  const estimatedTokens = useMemo(() => {
    const text = [form.personality, form.appearance, form.speech_pattern, form.backstory, form.hidden_layers, form.inner_conflict, companionEnabled ? form.companion_personality : '', companionEnabled ? form.companion_appearance : '', companionEnabled ? form.companion_speech_pattern : '', companionEnabled ? form.companion_backstory : '', form.scenario, form.greeting_message, form.example_dialogues].join(' ');
    const hasCyrillic = /[\u0400-\u04FF]/.test(text);
    return Math.round(text.length / (hasCyrillic ? 2 : 4));
  }, [form.personality, form.appearance, form.speech_pattern, form.backstory, form.hidden_layers, form.inner_conflict, form.companion_personality, form.companion_appearance, form.companion_speech_pattern, form.companion_backstory, companionEnabled, form.scenario, form.greeting_message, form.example_dialogues]);

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
        backstory: form.backstory || undefined,
        hidden_layers: form.hidden_layers || undefined,
        inner_conflict: form.inner_conflict || undefined,
        companion_name: companionEnabled ? (form.companion_name || undefined) : null,
        companion_role: companionEnabled ? (form.companion_role || undefined) : null,
        companion_personality: companionEnabled ? (form.companion_personality || undefined) : null,
        companion_appearance: companionEnabled ? (form.companion_appearance || undefined) : null,
        companion_avatar_url: companionEnabled ? (form.companion_avatar_url || undefined) : null,
        companion_speech_pattern: companionEnabled ? (form.companion_speech_pattern || undefined) : null,
        companion_backstory: companionEnabled ? (form.companion_backstory || undefined) : null,
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
        ...(isAdmin ? { preferred_model: form.preferred_model } : {}),
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
                          ? 'bg-purple-600 text-white'
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
        label={t('form.speechPattern')}
        hint={t('form.speechPatternHint')}
        value={form.speech_pattern}
        onChange={(e) => update('speech_pattern', e.target.value)}
        placeholder={t('form.speechPatternPlaceholder')}
        rows={2}
        maxLength={3000}
      />

      <Textarea
        label={t('form.backstory')}
        hint={t('form.backstoryHint')}
        value={form.backstory}
        onChange={(e) => update('backstory', e.target.value)}
        placeholder={t('form.backstoryPlaceholder')}
        rows={3}
        maxLength={5000}
      />

      <Textarea
        label={t('form.hiddenLayers')}
        hint={t('form.hiddenLayersHint')}
        value={form.hidden_layers}
        onChange={(e) => update('hidden_layers', e.target.value)}
        placeholder={t('form.hiddenLayersPlaceholder')}
        rows={3}
        maxLength={5000}
      />

      <Textarea
        label={t('form.innerConflict')}
        hint={t('form.innerConflictHint')}
        value={form.inner_conflict}
        onChange={(e) => update('inner_conflict', e.target.value)}
        placeholder={t('form.innerConflictPlaceholder')}
        rows={2}
        maxLength={2000}
      />

      {/* NPC Companion toggle + fields */}
      <div className="border-t border-neutral-800 pt-4 mt-2">
        <label className="flex items-center gap-2 cursor-pointer mb-3">
          <input
            type="checkbox"
            checked={companionEnabled}
            onChange={(e) => setCompanionEnabled(e.target.checked)}
            className="w-4 h-4 rounded border-neutral-600 bg-neutral-800 text-purple-500 focus:ring-purple-500"
          />
          <span className="text-sm text-neutral-300">{t('form.companionToggle')}</span>
          <span className="text-xs text-neutral-500">{t('form.companionToggleHint')}</span>
        </label>

        {companionEnabled && (
          <div className="space-y-3 pl-2 border-l-2 border-neutral-700">
            <Input
              label={t('form.companionName')}
              value={form.companion_name}
              onChange={(e) => update('companion_name', e.target.value)}
              placeholder={t('form.companionNamePlaceholder')}
              maxLength={100}
            />

            {form.companion_name && (
              <div>
                <label className="block text-sm text-neutral-400 mb-1">{t('form.companionAvatarHint')}</label>
                <AvatarUpload
                  currentUrl={form.companion_avatar_url || null}
                  name={form.companion_name || '?'}
                  onChange={(url) => setForm((prev) => ({ ...prev, companion_avatar_url: url }))}
                  isAdmin={isAdmin}
                  characterDescription={form.companion_appearance || form.companion_name || ''}
                />
              </div>
            )}

            <div>
              <label className="block text-sm text-neutral-400 mb-1">
                {t('form.companionRole')}
              </label>
              <select
                value={form.companion_role}
                onChange={(e) => update('companion_role', e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-200"
              >
                <option value="">{t('form.companionRoleNone')}</option>
                <option value="sidekick">{t('form.companionRoleSidekick')}</option>
                <option value="rival">{t('form.companionRoleRival')}</option>
                <option value="mentor">{t('form.companionRoleMentor')}</option>
                <option value="pet">{t('form.companionRolePet')}</option>
                <option value="lover">{t('form.companionRoleLover')}</option>
                <option value="family">{t('form.companionRoleFamily')}</option>
                <option value="guide">{t('form.companionRoleGuide')}</option>
                <option value="comic_relief">{t('form.companionRoleComic')}</option>
              </select>
            </div>

            <Textarea
              label={t('form.companionPersonality')}
              hint={t('form.companionPersonalityHint')}
              value={form.companion_personality}
              onChange={(e) => update('companion_personality', e.target.value)}
              placeholder={t('form.companionPersonalityPlaceholder')}
              rows={2}
              maxLength={500}
            />

            <Textarea
              label={t('form.companionAppearance')}
              hint={t('form.companionAppearanceHint')}
              value={form.companion_appearance}
              onChange={(e) => update('companion_appearance', e.target.value)}
              placeholder={t('form.companionAppearancePlaceholder')}
              rows={2}
              maxLength={300}
            />

            <Textarea
              label={t('form.companionSpeechPattern')}
              hint={t('form.companionSpeechPatternHint')}
              value={form.companion_speech_pattern}
              onChange={(e) => update('companion_speech_pattern', e.target.value)}
              placeholder={t('form.companionSpeechPatternPlaceholder')}
              rows={2}
              maxLength={300}
            />

            <Textarea
              label={t('form.companionBackstory')}
              hint={t('form.companionBackstoryHint')}
              value={form.companion_backstory}
              onChange={(e) => update('companion_backstory', e.target.value)}
              placeholder={t('form.companionBackstoryPlaceholder')}
              rows={2}
              maxLength={500}
            />
          </div>
        )}
      </div>

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
        hint={t('form.greetingHint')}
        value={form.greeting_message}
        onChange={(e) => update('greeting_message', e.target.value)}
        placeholder={t('form.greetingPlaceholder')}
        rows={3}
        maxLength={5000}
        required
      />

      <Textarea
        label={t('form.exampleDialogues')}
        hint={t('form.exampleDialoguesHint')}
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
          </select>
        </div>

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
              className="w-4 h-4 rounded accent-purple-600"
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
          className="w-full accent-purple-500"
        />
        <p className="text-xs text-neutral-500 mt-1">
          {t('form.maxTokensHelp')}
        </p>
      </div>
      )}

      {/* Token budget indicator */}
      {estimatedTokens > 0 && (
        <div className={`text-xs text-center ${estimatedTokens > 2000 ? 'text-amber-400' : estimatedTokens > 3000 ? 'text-red-400' : 'text-neutral-500'}`}>
          {t('form.tokenBudget', { tokens: estimatedTokens })}
        </div>
      )}

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? t('common.saving') : (submitLabel || t('common.create'))}
      </Button>
    </form>
  );
}
