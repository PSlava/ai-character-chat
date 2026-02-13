import { useState, useEffect, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createCharacter, generateFromStory, getOpenRouterModels, wakeUpServer } from '@/api/characters';
import type { OpenRouterModel } from '@/api/characters';
import { importCharacter } from '@/api/export';
import { CharacterForm } from '@/components/characters/CharacterForm';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Input } from '@/components/ui/Input';
import { Upload } from 'lucide-react';
import type { Character } from '@/types';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

type Tab = 'manual' | 'from-story' | 'import';

export function CreateCharacterPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const authUser = useAuthStore((s) => s.user);
  const isAdmin = authUser?.role === 'admin';
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
  const [importJson, setImportJson] = useState('');
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      navigate(character.slug ? `/c/${character.slug}` : `/character/${character.id}`);
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

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      setImportJson(text);
    };
    reader.readAsText(file);
    // Reset input so the same file can be selected again
    e.target.value = '';
  };

  const handleImport = async () => {
    if (!importJson.trim()) return;
    setImporting(true);
    setError('');
    try {
      const card = JSON.parse(importJson);
      const result = await importCharacter(card);
      toast.success(t('create.importSuccess'));
      navigate(result.slug ? `/c/${result.slug}` : `/character/${result.id}`);
    } catch (e: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ax = e as any;
      if (ax instanceof SyntaxError) {
        setError(t('create.importError'));
      } else {
        const detail = ax?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : t('create.importError'));
      }
    } finally {
      setImporting(false);
    }
  };

  if (!authLoading && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">{t('create.title')}</h1>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('manual')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'manual'
              ? 'bg-rose-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          {t('create.tabManual')}
        </button>
        <button
          onClick={() => setTab('from-story')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'from-story'
              ? 'bg-rose-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          {t('create.tabFromText')}
        </button>
        <button
          onClick={() => setTab('import')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === 'import'
              ? 'bg-rose-600 text-white'
              : 'bg-neutral-800 text-neutral-400 hover:text-white'
          }`}
        >
          {t('create.tabImport')}
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
            maxLength={50000}
            required
          />

          <Input
            label={t('create.nameOptional')}
            value={characterName}
            onChange={(e) => setCharacterName(e.target.value)}
            placeholder={t('create.nameHint')}
            maxLength={100}
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
            maxLength={2000}
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

      {tab === 'import' && (
        <div className="space-y-4 max-w-2xl">
          <h2 className="text-lg font-semibold">{t('create.importTitle')}</h2>
          <p className="text-sm text-neutral-400">{t('create.importHint')}</p>

          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            onChange={handleFileUpload}
            className="hidden"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="w-full border-2 border-dashed border-neutral-700 hover:border-neutral-500 rounded-xl p-8 flex flex-col items-center gap-3 text-neutral-400 hover:text-neutral-300 transition-colors"
          >
            <Upload className="w-8 h-8" />
            <span className="text-sm">
              {importJson ? t('create.importSuccess').split('!')[0] : t('create.importHint')}
            </span>
          </button>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">
              {t('create.importPaste')}
            </label>
            <textarea
              value={importJson}
              onChange={(e) => setImportJson(e.target.value)}
              placeholder={t('create.importPastePlaceholder')}
              rows={10}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white text-sm font-mono resize-y"
            />
          </div>

          <Button
            onClick={handleImport}
            disabled={importing || !importJson.trim()}
            className="w-full"
          >
            {importing ? t('create.importing') : t('create.importButton')}
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
            isAdmin={isAdmin}
          />
        </>
      )}
    </div>
  );
}
