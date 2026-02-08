import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createCharacter, generateFromStory, getOpenRouterModels, wakeUpServer } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import { CharacterForm } from '@/components/characters/CharacterForm';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Input } from '@/components/ui/Input';
import type { Character } from '@/types';

type Tab = 'manual' | 'from-story';

export function CreateCharacterPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('manual');
  const [storyText, setStoryText] = useState('');
  const [characterName, setCharacterName] = useState('');
  const [model, setModel] = useState('openrouter');
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
    const character = await createCharacter(data);
    navigate(`/character/${character.id}`);
  };

  const handleGenerate = async () => {
    if (!storyText.trim()) return;
    setGenerating(true);
    setError('');
    setStatusText('');
    try {
      setStatusText('Проверка сервера...');
      await wakeUpServer((s) => setStatusText(s));
      setStatusText('Генерация... (может занять 10-30 сек)');
      const data = await generateFromStory(storyText, characterName, model, contentRating, extraInstructions);
      setGenerated(data);
      setTab('manual');
    } catch (e: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ax = e as any;
      const msg = ax?.response?.data?.detail
        || ax?.message
        || 'Ошибка генерации';
      setError(msg);
    } finally {
      setGenerating(false);
      setStatusText('');
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Создать персонажа</h1>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('manual')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'manual'
              ? 'bg-purple-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          Вручную
        </button>
        <button
          onClick={() => setTab('from-story')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'from-story'
              ? 'bg-purple-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          Из текста
        </button>
      </div>

      {tab === 'from-story' && (
        <div className="space-y-4 max-w-2xl">
          <Textarea
            label="Текст рассказа / описание персонажа"
            value={storyText}
            onChange={(e) => setStoryText(e.target.value)}
            placeholder="Вставьте текст рассказа, описание персонажа или любой текст, на основе которого нужно создать персонажа..."
            rows={10}
            required
          />

          <Input
            label="Имя персонажа (необязательно)"
            value={characterName}
            onChange={(e) => setCharacterName(e.target.value)}
            placeholder="Если не указать — AI выберет самого интересного"
          />

          <div>
            <label className="block text-sm text-neutral-400 mb-1">
              AI Модель
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white w-full"
            >
              <option value="openrouter">OpenRouter Auto (Free) — автовыбор лучшей</option>
              {orModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.quality}/10) — {m.note}
                </option>
              ))}
              <option disabled>───────────</option>
              <option value="deepseek">DeepSeek (deepseek-chat)</option>
              <option value="qwen">Qwen (qwen3-32b)</option>
              <option disabled>───────────</option>
              <option value="gemini">Gemini (платная)</option>
              <option value="claude">Claude (платная)</option>
              <option value="openai">GPT-4o (платная)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">
              Рейтинг контента
            </label>
            <select
              value={contentRating}
              onChange={(e) => setContentRating(e.target.value)}
              className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white"
            >
              <option value="sfw">SFW — безопасный контент</option>
              <option value="moderate">Moderate — умеренный (насилие, мрачные темы)</option>
              <option value="nsfw">NSFW — взрослый контент</option>
            </select>
          </div>

          <Textarea
            label="Дополнительные пожелания (необязательно)"
            value={extraInstructions}
            onChange={(e) => setExtraInstructions(e.target.value)}
            placeholder="Например: сделай персонажа более саркастичным, добавь акцент, пусть говорит на ты..."
            rows={3}
          />

          {error && (
            <div className="text-red-400 text-sm bg-red-900/20 p-3 rounded-lg">
              {error}
            </div>
          )}

          <Button
            onClick={handleGenerate}
            disabled={generating || !storyText.trim()}
            className="w-full"
          >
            {generating ? (statusText || 'Генерация...') : 'Сгенерировать персонажа'}
          </Button>
        </div>
      )}

      {tab === 'manual' && (
        <CharacterForm
          key={generated ? 'generated' : 'empty'}
          initial={generated || undefined}
          onSubmit={handleSubmit}
          submitLabel="Создать персонажа"
        />
      )}
    </div>
  );
}
