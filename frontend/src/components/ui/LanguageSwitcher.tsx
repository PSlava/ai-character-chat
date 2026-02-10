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

  if (compact) {
    return (
      <div className="flex items-center gap-0.5 text-sm">
        <button
          onClick={() => change('ru')}
          className={`px-1.5 py-0.5 rounded transition-colors ${
            lang === 'ru' ? 'text-white font-medium' : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          RU
        </button>
        <span className="text-neutral-600">|</span>
        <button
          onClick={() => change('en')}
          className={`px-1.5 py-0.5 rounded transition-colors ${
            lang === 'en' ? 'text-white font-medium' : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          EN
        </button>
      </div>
    );
  }

  return (
    <select
      value={lang}
      onChange={(e) => change(e.target.value)}
      className="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white"
    >
      <option value="ru">{t('lang.ru')}</option>
      <option value="en">{t('lang.en')}</option>
    </select>
  );
}
