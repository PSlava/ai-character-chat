import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Star } from 'lucide-react';
import { rateAdventure } from '@/api/chat';
import toast from 'react-hot-toast';

interface Props {
  chatId: string;
  existingRating?: number | null;
  onRated?: (rating: number) => void;
}

export function RatingPrompt({ chatId, existingRating, onRated }: Props) {
  const { t } = useTranslation();
  const [hover, setHover] = useState(0);
  const [rating, setRating] = useState(existingRating || 0);
  const [submitted, setSubmitted] = useState(!!existingRating);

  if (submitted && rating) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-800/50 text-sm text-neutral-400">
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5].map((s) => (
            <Star key={s} className={`w-4 h-4 ${s <= rating ? 'fill-amber-400 text-amber-400' : 'text-neutral-600'}`} />
          ))}
        </div>
        <span>{t('rating.thanks')}</span>
      </div>
    );
  }

  const handleRate = async (value: number) => {
    setRating(value);
    try {
      await rateAdventure(chatId, value);
      setSubmitted(true);
      onRated?.(value);
      toast.success(t('rating.thanks'));
    } catch {
      toast.error('Failed to rate');
    }
  };

  return (
    <div className="flex flex-col items-center gap-2 px-4 py-3 rounded-lg bg-neutral-800/60 border border-neutral-700/50">
      <span className="text-sm text-neutral-300">{t('rating.prompt')}</span>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((s) => (
          <button
            key={s}
            onClick={() => handleRate(s)}
            onMouseEnter={() => setHover(s)}
            onMouseLeave={() => setHover(0)}
            className="p-1 transition-transform hover:scale-110"
          >
            <Star
              className={`w-6 h-6 transition-colors ${
                s <= (hover || rating)
                  ? 'fill-amber-400 text-amber-400'
                  : 'text-neutral-500 hover:text-neutral-400'
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  );
}
