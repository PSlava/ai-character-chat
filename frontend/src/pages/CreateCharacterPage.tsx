import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createCharacter, generateFromStory, getOpenRouterModels, wakeUpServer } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import { CharacterForm } from '@/components/characters/CharacterForm';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Input } from '@/components/ui/Input';
import type { Character } from '@/types';

type Tab = 'manual' | 'from-story';

export function CreateCharacterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('manual');
  const [storyText, setStoryText] = useState('');
  const [characterName, setCharacterName] = useState('');
  const [model, setModel] = useState('qwen');
  const [contentRating, setContentRating] = useState('sfw');
  const [extraInstructions, setExtraInstructions] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [statusText, setStatusText] = useState('');
  const [generated, setGenerated] = useState<Partial<Character> | null>(null);
  const [orModels, setOrModels] = useState<OpenRouterModel[]>([]);

  useEffect(() => {
    getOpenRouterModels()
      .then(setOrModels)
      .catch(() => {
        // Server might be sleeping — try waking it up
        wakeUpServer()
          .then(() => getOpenRouterModels())
          .then(setOrModels)
          .catch(() => {});
      });
  }, []);

  const handleSubmit = async (data: Partial<Character>) => {
    setError('');
    try {
      setStatusText(t('create.checkingServer'));
      await wakeUpServer((s) => setStatusText(s));
      setStatusText('');
      const character = await createCharacter(data);
      navigate(`/character/${character.id}`);
    } catch (e: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ax = e as any;
      const detail = ax?.response?.data?.detail;
      let msg: string;
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ');
      } else {
        msg = ax?.message || t('create.saveError');
      }
      console.error('Save error:', ax?.response?.status, detail || ax?.message);
      setError(msg);
    }
  };

  const handleGenerate = async () => {
    if (!storyText.trim()) return;
    setGenerating(true);
    setError('');
    setStatusText('');
    try {
      setStatusText(t('create.checkingServer'));
      await wakeUpServer((s) => setStatusText(s));
      setStatusText(t('create.generating'));
      const data = await generateFromStory(storyText, characterName, model, contentRating, extraInstructions);
      setGenerated(data);
      setTab('manual');
    } catch (e: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ax = e as any;
      const detail = ax?.response?.data?.detail;
      let msg: string;
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ');
      } else {
        msg = ax?.message || t('create.generateError');
      }
      setError(msg);
    } finally {
      setGenerating(false);
      setStatusText('');
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">{t('create.title')}</h1>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('manual')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'manual'
              ? 'bg-purple-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          {t('create.tabManual')}
        </button>
        <button
          onClick={() => setTab('from-story')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'from-story'
              ? 'bg-purple-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          {t('create.tabFromText')}
        </button>
      </div>

      {error && (
        <div className="text-red-400 text-sm bg-red-900/20 p-3 rounded-lg mb-4 max-w-2xl">
          {error}
        </div>
      )}

      {tab === 'from-story' && (
        <div className="space-y-4 max-w-2xl">
          <Textarea
            label={t('create.storyLabel')}
            value={storyText}
            onChange={(e) => setStoryText(e.target.value)}
            placeholder={t('create.storyPlaceholder')}
            rows={10}
            required
          />

          <Input
            label={t('create.nameOptional')}
            value={characterName}
            onChange={(e) => setCharacterName(e.target.value)}
            placeholder={t('create.nameHint')}
          />

          <div>
            <label className="block text-sm text-neutral-400 mb-1">
              {t('create.aiModel')}
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white w-full"
            >
              <option value="openrouter">{t('create.openrouterAuto')}</option>
              {orModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.quality}/10) — {m.note}
                </option>
              ))}
              <option disabled>───────────</option>
              <option value="deepseek">{t('create.deepseek')}</option>
              <option value="qwen">{t('create.qwen')}</option>
              <option disabled>───────────</option>
              <option value="gemini">{t('create.geminiPaid')}</option>
              <option value="claude">{t('create.claudePaid')}</option>
              <option value="openai">{t('create.gptPaid')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">
              {t('create.contentRating')}
            </label>
            <select
              value={contentRating}
              onChange={(e) => setContentRating(e.target.value)}
              className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white"
            >
              <option value="sfw">{t('create.sfwLabel')}</option>
              <option value="moderate">{t('create.moderateLabel')}</option>
              <option value="nsfw">{t('create.nsfwLabel')}</option>
            </select>
          </div>

          <Textarea
            label={t('create.extraWishes')}
            value={extraInstructions}
            onChange={(e) => setExtraInstructions(e.target.value)}
            placeholder={t('create.extraPlaceholder')}
            rows={3}
          />

          <Button
            onClick={handleGenerate}
            disabled={generating || !storyText.trim()}
            className="w-full"
          >
            {generating ? (statusText || t('create.generating')) : t('create.generateButton')}
          </Button>
        </div>
      )}

      {tab === 'manual' && (
        <>
          {statusText && (
            <div className="text-neutral-400 text-sm mb-4">{statusText}</div>
          )}
          <CharacterForm
            key={generated ? 'generated' : 'empty'}
            initial={generated || undefined}
            onSubmit={handleSubmit}
            submitLabel={t('create.createButton')}
          />
        </>
      )}
    </div>
  );
}
