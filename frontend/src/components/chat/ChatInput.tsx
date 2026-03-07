import { useState, useRef, useEffect, useCallback, KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Send, Square, Sparkles } from 'lucide-react';

interface Props {
  onSend: (content: string) => void;
  onStop?: () => void;
  isStreaming: boolean;
  disabled?: boolean;
  personaName?: string | null;
  onGeneratePersonaReply?: () => Promise<string | null>;
  prefillText?: string;
  onPrefillConsumed?: () => void;
}

export function ChatInput({ onSend, onStop, isStreaming, disabled, personaName, onGeneratePersonaReply, prefillText, onPrefillConsumed }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  const [generating, setGenerating] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [inputMode, setInputMode] = useState<'free' | 'action' | 'dialogue'>(() =>
    (localStorage.getItem('chat-input-mode') as 'free' | 'action' | 'dialogue') || 'free'
  );

  const autoSendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prefillRef = useRef('');

  const cancelAutoSend = useCallback(() => {
    if (autoSendTimer.current) {
      clearTimeout(autoSendTimer.current);
      autoSendTimer.current = null;
    }
    prefillRef.current = '';
  }, []);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 192)}px`; // 192px = max-h-48
  }, []);

  useEffect(() => {
    autoResize();
  }, [text, autoResize]);

  useEffect(() => {
    if (prefillText) {
      cancelAutoSend();
      setText(prefillText);
      prefillRef.current = prefillText;
      onPrefillConsumed?.();
      // Auto-send after 2s if user doesn't edit or interact
      autoSendTimer.current = setTimeout(() => {
        if (prefillRef.current) {
          prefillRef.current = '';
          onSend(prefillText);
          setText('');
        }
      }, 2000);
    }
  }, [prefillText]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup timer on unmount
  useEffect(() => () => cancelAutoSend(), [cancelAutoSend]);

  const cycleMode = (mode: 'free' | 'action' | 'dialogue') => {
    setInputMode(mode);
    localStorage.setItem('chat-input-mode', mode);
  };

  const wrapWithMode = (t: string) => {
    if (inputMode === 'action') return `*${t}*`;
    if (inputMode === 'dialogue') return `"${t}"`;
    return t;
  };

  const handleSend = () => {
    const isSuggestion = !!(prefillRef.current && prefillRef.current === text.trim());
    cancelAutoSend();
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    onSend(isSuggestion ? trimmed : wrapWithMode(trimmed));
    setText('');
    // Reset height after send
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    });
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleGenerate = async () => {
    if (!onGeneratePersonaReply || generating || isStreaming) return;
    setGenerating(true);
    try {
      const result = await onGeneratePersonaReply();
      if (result) {
        setText(result);
        requestAnimationFrame(() => {
          textareaRef.current?.focus();
        });
      }
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="border-t border-neutral-800 p-2 sm:p-4">
      <div className="flex gap-1 mb-1.5 max-w-3xl mx-auto px-1">
        {(['free', 'action', 'dialogue'] as const).map(mode => (
          <button
            key={mode}
            onClick={() => cycleMode(mode)}
            title={t(`chat.mode${mode.charAt(0).toUpperCase() + mode.slice(1)}Tooltip`)}
            className={`px-2 py-0.5 text-xs rounded-md transition-colors ${
              inputMode === mode
                ? 'bg-rose-600/20 text-rose-400 border border-rose-500/30'
                : 'text-neutral-500 hover:text-neutral-300'
            }`}
          >
            {mode === 'free' ? '\u270D\uFE0F' : mode === 'action' ? '\u26A1' : '\uD83D\uDCAC'} {t(`chat.mode${mode.charAt(0).toUpperCase() + mode.slice(1)}`)}
          </button>
        ))}
      </div>
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        {personaName && onGeneratePersonaReply && (
          <button
            onClick={handleGenerate}
            disabled={generating || isStreaming || disabled}
            className="p-3 text-purple-400 hover:text-purple-300 hover:bg-purple-900/20 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title={t('chat.generateAsPersona')}
          >
            <Sparkles className={`w-5 h-5 ${generating ? 'animate-pulse' : ''}`} />
          </button>
        )}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => { cancelAutoSend(); setText(e.target.value); }}
          onKeyDown={handleKeyDown}
          onPointerDown={cancelAutoSend}
          placeholder={t('chat.placeholder')}
          rows={1}
          disabled={disabled}
          className="flex-1 bg-neutral-800 border border-neutral-700 rounded-xl px-4 py-3 text-white placeholder-neutral-500 focus:outline-none focus:border-rose-500 resize-none max-h-48 overflow-y-auto"
          style={{ scrollbarWidth: 'none' }}
        />
        {isStreaming ? (
          <button
            onClick={onStop}
            className="p-3 bg-red-600 hover:bg-red-700 rounded-xl transition-colors"
          >
            <Square className="w-5 h-5" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!text.trim() || disabled}
            className="p-3 bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}
