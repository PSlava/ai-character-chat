import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getLoreEntries, createLoreEntry, updateLoreEntry, deleteLoreEntry } from '@/api/lore';
import type { LoreEntry } from '@/api/lore';
import { Plus, Trash2, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import toast from 'react-hot-toast';

interface LoreEditorProps {
  characterId: string;
}

export function LoreEditor({ characterId }: LoreEditorProps) {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<LoreEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getLoreEntries(characterId)
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [characterId]);

  const handleAdd = async () => {
    try {
      const entry = await createLoreEntry(characterId, {
        keywords: '',
        content: '',
        position: entries.length,
      });
      setEntries((prev) => [...prev, entry]);
      setExpanded(entry.id);
    } catch {
      toast.error(t('lore.errorCreating'));
    }
  };

  const handleUpdate = async (entryId: string, field: string, value: string | boolean) => {
    try {
      const updated = await updateLoreEntry(characterId, entryId, { [field]: value });
      setEntries((prev) => prev.map((e) => (e.id === entryId ? updated : e)));
    } catch {
      toast.error(t('lore.errorSaving'));
    }
  };

  const handleDelete = async (entryId: string) => {
    try {
      await deleteLoreEntry(characterId, entryId);
      setEntries((prev) => prev.filter((e) => e.id !== entryId));
      toast.success(t('lore.deleted'));
    } catch {
      toast.error(t('lore.errorDeleting'));
    }
  };

  if (loading) {
    return <div className="text-neutral-500 text-sm">{t('common.loading')}</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-neutral-400" />
          <h3 className="text-lg font-semibold">{t('lore.title')}</h3>
          <span className="text-neutral-500 text-sm">({entries.length}/50)</span>
        </div>
        {entries.length < 50 && (
          <button
            onClick={handleAdd}
            className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t('lore.add')}
          </button>
        )}
      </div>

      <p className="text-neutral-500 text-sm mb-4">{t('lore.hint')}</p>

      {entries.length === 0 ? (
        <p className="text-neutral-600 text-sm italic">{t('lore.empty')}</p>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="border border-neutral-700 rounded-lg bg-neutral-800/50 overflow-hidden"
            >
              {/* Header row */}
              <div
                className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-neutral-800/80"
                onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
              >
                <label className="flex items-center" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={entry.enabled}
                    onChange={(e) => handleUpdate(entry.id, 'enabled', e.target.checked)}
                    className="rounded bg-neutral-700 border-neutral-600 text-rose-500 focus:ring-rose-500"
                  />
                </label>
                <div className="flex-1 min-w-0">
                  <span className={`text-sm truncate ${entry.enabled ? 'text-white' : 'text-neutral-500'}`}>
                    {entry.keywords || t('lore.noKeywords')}
                  </span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(entry.id); }}
                  className="p-1 rounded hover:bg-red-900/50 text-neutral-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                {expanded === entry.id ? (
                  <ChevronUp className="w-4 h-4 text-neutral-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-neutral-500" />
                )}
              </div>

              {/* Expanded content */}
              {expanded === entry.id && (
                <div className="px-4 pb-4 space-y-3 border-t border-neutral-700">
                  <div className="mt-3">
                    <label className="block text-xs text-neutral-400 mb-1">{t('lore.keywords')}</label>
                    <input
                      type="text"
                      value={entry.keywords}
                      onChange={(e) => setEntries((prev) => prev.map((en) => en.id === entry.id ? { ...en, keywords: e.target.value } : en))}
                      onBlur={(e) => handleUpdate(entry.id, 'keywords', e.target.value)}
                      placeholder={t('lore.keywordsPlaceholder')}
                      className="w-full px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-lg text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-rose-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-neutral-400 mb-1">{t('lore.content')}</label>
                    <textarea
                      value={entry.content}
                      onChange={(e) => setEntries((prev) => prev.map((en) => en.id === entry.id ? { ...en, content: e.target.value } : en))}
                      onBlur={(e) => handleUpdate(entry.id, 'content', e.target.value)}
                      placeholder={t('lore.contentPlaceholder')}
                      rows={4}
                      className="w-full px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-lg text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-rose-500 resize-y"
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
