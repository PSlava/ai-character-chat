import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, Loader2, Wand2 } from 'lucide-react';
import { uploadAvatar, generateAvatar } from '@/api/uploads';
import { Avatar } from './Avatar';

interface Props {
  currentUrl?: string | null;
  name: string;
  onChange: (url: string) => void;
  required?: boolean;
  isAdmin?: boolean;
  characterDescription?: string;
}

export function AvatarUpload({ currentUrl, name, onChange, required, isAdmin, characterDescription }: Props) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [showPrompt, setShowPrompt] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError('');
    setUploading(true);
    try {
      const url = await uploadAvatar(file);
      onChange(url);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(ax?.response?.data?.detail || t('common.uploadError'));
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setError('');
    setGenerating(true);
    try {
      const url = await generateAvatar(prompt.trim());
      onChange(url);
      setShowPrompt(false);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(ax?.response?.data?.detail || t('common.uploadError'));
    } finally {
      setGenerating(false);
    }
  };

  const openPromptInput = () => {
    if (!showPrompt) {
      const desc = (characterDescription || '').slice(0, 300).trim();
      setPrompt(
        desc
          ? `Digital art portrait of ${desc}. Fantasy style, detailed, bust shot.`
          : 'Digital art portrait of a character. Fantasy style, detailed, bust shot.'
      );
    }
    setShowPrompt(!showPrompt);
  };

  const needsAvatar = required && !currentUrl;

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className={`relative group cursor-pointer rounded-full ${
          needsAvatar ? 'ring-2 ring-dashed ring-red-500/60' : ''
        }`}
      >
        <Avatar src={currentUrl} name={name} size="lg" />
        <div className="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          {uploading ? (
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          ) : (
            <Camera className="w-6 h-6 text-white" />
          )}
        </div>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        onChange={handleFileChange}
        className="hidden"
      />
      <span className={`text-xs ${needsAvatar ? 'text-red-400 font-medium' : 'text-neutral-500'}`}>
        {needsAvatar ? t('form.avatarRequired') : t('form.avatarHint')}
      </span>

      {isAdmin && (
        <div className="flex flex-col items-center gap-1.5 w-full max-w-xs">
          <button
            type="button"
            onClick={openPromptInput}
            disabled={generating}
            className="flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 transition-colors"
          >
            <Wand2 className="w-3.5 h-3.5" />
            {t('form.generateAvatar')}
          </button>
          {showPrompt && (
            <div className="w-full space-y-1.5">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={3}
                maxLength={1000}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white resize-none focus:outline-none focus:border-purple-500"
                placeholder={t('form.avatarPrompt')}
              />
              <button
                type="button"
                onClick={handleGenerate}
                disabled={generating || !prompt.trim()}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-xs text-white transition-colors"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    {t('form.generating')}
                  </>
                ) : (
                  <>
                    <Wand2 className="w-3.5 h-3.5" />
                    {t('form.generateAvatar')}
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}
