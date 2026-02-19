import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getCharacters } from '@/api/characters';
import { createGroupChat } from '@/api/groupChat';
import { useGroupChatStore } from '@/store/groupChatStore';
import { Avatar } from '@/components/ui/Avatar';
import { Search, X, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import type { Character } from '@/types';

interface Props {
  onClose: () => void;
}

export function CreateGroupChatModal({ onClose }: Props) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { addGroupChat } = useGroupChatStore();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCharacters({ language: i18n.language, limit: 100 })
      .then((res) => {
        setCharacters(res.items);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [i18n.language]);

  const filtered = characters.filter(
    (c) => c.name.toLowerCase().includes(search.toLowerCase())
  );

  const toggleSelect = (id: string) => {
    setSelected((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length < 3
          ? [...prev, id]
          : prev
    );
  };

  const handleCreate = async () => {
    if (selected.length < 2) {
      toast.error(t('groupChat.minCharacters'));
      return;
    }
    setCreating(true);
    try {
      const gc = await createGroupChat(selected);
      addGroupChat(gc);
      onClose();
      navigate(`/group-chat/${gc.id}`);
    } catch {
      toast.error(t('chat.generationError'));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-neutral-900 border border-neutral-700 rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-800">
          <h2 className="text-lg font-semibold">{t('groupChat.create')}</h2>
          <button onClick={onClose} className="p-1 text-neutral-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 pb-2">
          <p className="text-sm text-neutral-400 mb-3">{t('groupChat.selectCharacters')}</p>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('groupChat.searchPlaceholder')}
              className="w-full pl-9 pr-4 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-rose-500"
            />
          </div>
          {selected.length > 0 && (
            <p className="text-xs text-rose-400 mt-2">
              {t('groupChat.selected', { count: selected.length })} / 3
            </p>
          )}
        </div>

        {/* Character list */}
        <div className="flex-1 overflow-y-auto p-4 pt-2 space-y-1">
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2">
                  <div className="w-10 h-10 rounded-full animate-pulse bg-neutral-700/50" />
                  <div className="h-4 rounded animate-pulse bg-neutral-700/50 flex-1" />
                </div>
              ))}
            </div>
          ) : (
            filtered.map((c) => {
              const isSelected = selected.includes(c.id);
              return (
                <button
                  key={c.id}
                  onClick={() => toggleSelect(c.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    isSelected
                      ? 'bg-rose-600/20 border border-rose-600/40'
                      : 'hover:bg-neutral-800 border border-transparent'
                  }`}
                >
                  <Avatar src={c.avatar_url} name={c.name} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{c.name}</p>
                    {c.tagline && (
                      <p className="text-xs text-neutral-500 truncate">{c.tagline}</p>
                    )}
                  </div>
                  {isSelected && (
                    <Check className="w-4 h-4 text-rose-400 shrink-0" />
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-800 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl border border-neutral-700 text-neutral-300 hover:bg-neutral-800 transition-colors"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleCreate}
            disabled={selected.length < 2 || creating}
            className="flex-1 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white transition-colors"
          >
            {creating ? t('groupChat.creating') : t('common.create')}
          </button>
        </div>
      </div>
    </div>
  );
}
