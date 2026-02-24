import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, ChevronRight } from 'lucide-react';

const GENDER_OPTIONS = [
  { key: 'female', emoji: '♀', labelKey: 'onboarding.female' },
  { key: 'male', emoji: '♂', labelKey: 'onboarding.male' },
  { key: 'both', emoji: '⚤', labelKey: 'onboarding.both' },
];

const TAG_OPTIONS = [
  { key: 'фэнтези', labelKey: 'tags.fantasy' },
  { key: 'романтика', labelKey: 'tags.romance' },
  { key: 'аниме', labelKey: 'tags.anime' },
  { key: 'современность', labelKey: 'tags.modern' },
];

export interface OnboardingPrefs {
  gender: string | null;
  tag: string | null;
}

export function getOnboardingPrefs(): OnboardingPrefs | null {
  try {
    const raw = localStorage.getItem('onboarding-prefs');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function OnboardingModal() {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  const [gender, setGender] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [visible, setVisible] = useState(() => !localStorage.getItem('onboarding-done'));

  if (!visible) return null;

  const handleFinish = () => {
    const prefs: OnboardingPrefs = {
      gender: gender === 'both' ? null : gender,
      tag: selectedTag,
    };
    localStorage.setItem('onboarding-prefs', JSON.stringify(prefs));
    localStorage.setItem('onboarding-done', '1');
    setVisible(false);
    window.dispatchEvent(new Event('onboarding-complete'));
  };

  const handleSkip = () => {
    localStorage.setItem('onboarding-done', '1');
    setVisible(false);
    window.dispatchEvent(new Event('onboarding-complete'));
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-neutral-900 border border-neutral-700 rounded-2xl w-full max-w-md overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="p-6 pb-2 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600/20 rounded-full mb-3">
            <Sparkles size={24} className="text-blue-400" />
          </div>
          <h2 className="text-xl font-bold text-white">{t('onboarding.title')}</h2>
          <p className="text-sm text-neutral-400 mt-1">{t('onboarding.subtitle')}</p>
        </div>

        <div className="p-6 pt-4">
          {step === 0 && (
            <>
              <p className="text-sm font-medium text-neutral-300 mb-3">{t('onboarding.genderQuestion')}</p>
              <div className="grid grid-cols-3 gap-2">
                {GENDER_OPTIONS.map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() => setGender(opt.key)}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all ${
                      gender === opt.key
                        ? 'border-blue-500 bg-blue-500/10 text-white'
                        : 'border-neutral-700 bg-neutral-800 text-neutral-400 hover:border-neutral-600 hover:text-neutral-200'
                    }`}
                  >
                    <span className="text-2xl">{opt.emoji}</span>
                    <span className="text-xs font-medium">{t(opt.labelKey)}</span>
                  </button>
                ))}
              </div>
              <button
                onClick={() => setStep(1)}
                disabled={!gender}
                className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors"
              >
                {t('onboarding.next')}
                <ChevronRight size={16} />
              </button>
            </>
          )}

          {step === 1 && (
            <>
              <p className="text-sm font-medium text-neutral-300 mb-3">{t('onboarding.tagQuestion')}</p>
              <div className="grid grid-cols-2 gap-2">
                {TAG_OPTIONS.map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() => setSelectedTag(selectedTag === opt.key ? null : opt.key)}
                    className={`px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                      selectedTag === opt.key
                        ? 'border-emerald-500 bg-emerald-500/10 text-white'
                        : 'border-neutral-700 bg-neutral-800 text-neutral-400 hover:border-neutral-600 hover:text-neutral-200'
                    }`}
                  >
                    {t(opt.labelKey)}
                  </button>
                ))}
              </div>
              <button
                onClick={handleFinish}
                className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors"
              >
                {t('onboarding.finish')}
                <Sparkles size={16} />
              </button>
            </>
          )}

          <button
            onClick={handleSkip}
            className="w-full mt-2 px-4 py-2 text-xs text-neutral-500 hover:text-neutral-300 transition-colors"
          >
            {t('onboarding.skip')}
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex justify-center gap-1.5 pb-4">
          {[0, 1].map((s) => (
            <div
              key={s}
              className={`w-1.5 h-1.5 rounded-full transition-colors ${
                s === step ? 'bg-blue-500' : 'bg-neutral-700'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
