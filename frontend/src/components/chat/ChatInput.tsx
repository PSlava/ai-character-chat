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
}

export function ChatInput({ onSend, onStop, isStreaming, disabled, personaName, onGeneratePersonaReply }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState('');
  const [generating, setGenerating] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 192)}px`; // 192px = max-h-48
  }, []);

  useEffect(() => {
    autoResize();
  }, [text, autoResize]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
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
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
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
