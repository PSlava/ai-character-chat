import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/store/authStore';
import { updateProfile } from '@/api/users';

interface Props {
  compact?: boolean;
}

export function LanguageSwitcher({ compact }: Props) {
  const { i18n, t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const lang = i18n.language;

  const change = async (newLang: string) => {
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
    if (user) {
      try { await updateProfile({ language: newLang }); } catch {}
    }
  };

  const langs = [
    { code: 'en', label: 'EN' },
    { code: 'es', label: 'ES' },
    { code: 'ru', label: 'RU' },
  ];

  if (compact) {
    return (
      <div className="flex items-center gap-0.5 text-sm">
        {langs.map((l, i) => (
          <span key={l.code} className="flex items-center">
            {i > 0 && <span className="text-neutral-600">|</span>}
            <button
              onClick={() => change(l.code)}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                lang === l.code ? 'text-white font-medium' : 'text-neutral-500 hover:text-neutral-300'
              }`}
            >
              {l.label}
            </button>
          </span>
        ))}
      </div>
    );
  }

  return (
    <select
      value={lang}
      onChange={(e) => change(e.target.value)}
      className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white"
    >
      {langs.map((l) => (
        <option key={l.code} value={l.code}>{t(`lang.${l.code}`)}</option>
      ))}
    </select>
  );
}
