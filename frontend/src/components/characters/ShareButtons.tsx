import { useTranslation } from 'react-i18next';
import { Link2, Check } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';

interface ShareButtonsProps {
  name: string;
  tagline?: string;
  url: string;
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function TelegramIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
    </svg>
  );
}

function RedditLogoIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M14.238 15.348c.085.084.085.221 0 .306-.465.462-1.194.687-2.231.687l-.008-.002-.008.002c-1.036 0-1.766-.225-2.231-.688-.085-.084-.085-.221 0-.305.084-.084.222-.084.307 0 .379.377 1.008.561 1.924.561l.008.002.008-.002c.915 0 1.544-.184 1.924-.561.085-.084.223-.084.307 0zm-3.44-2.418c0-.507-.414-.919-.922-.919-.509 0-.922.412-.922.919 0 .506.414.918.922.918.508 0 .922-.412.922-.918zm4.04-.919c-.509 0-.922.412-.922.919 0 .506.414.918.922.918.508 0 .922-.412.922-.918 0-.507-.414-.919-.922-.919zM12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.492 13.612c.018.162.028.326.028.494 0 2.512-2.926 4.55-6.534 4.55-3.608 0-6.534-2.038-6.534-4.55 0-.168.01-.332.028-.494a1.745 1.745 0 0 1-.7-1.396c0-.97.786-1.756 1.756-1.756.474 0 .904.19 1.218.498 1.198-.818 2.852-1.343 4.684-1.413l.886-4.163a.277.277 0 0 1 .332-.222l2.942.626a1.214 1.214 0 0 1 1.13-.766c.674 0 1.22.547 1.22 1.22 0 .674-.546 1.22-1.22 1.22-.674 0-1.22-.546-1.22-1.22l-2.644-.563-.79 3.72c1.814.078 3.443.601 4.627 1.41.315-.31.746-.5 1.222-.5.97 0 1.756.786 1.756 1.756 0 .6-.302 1.13-.762 1.449z" />
    </svg>
  );
}

export function ShareButtons({ name, tagline, url }: ShareButtonsProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const shareText = tagline ? `${name} — ${tagline}` : name;
  const encodedText = encodeURIComponent(shareText);
  const encodedUrl = encodeURIComponent(url);

  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`;
  const telegramUrl = `https://t.me/share/url?url=${encodedUrl}&text=${encodedText}`;
  const redditUrl = `https://reddit.com/submit?url=${encodedUrl}&title=${encodedText}`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success(t('share.linkCopied'));
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error(t('share.copyFailed'));
    }
  };

  const buttonClass =
    'p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors';

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-neutral-500 mr-1">{t('share.label')}</span>
      <a
        href={twitterUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={buttonClass}
        title="X (Twitter)"
      >
        <XIcon className="w-4 h-4" />
      </a>
      <a
        href={telegramUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={buttonClass}
        title="Telegram"
      >
        <TelegramIcon className="w-4 h-4" />
      </a>
      <a
        href={redditUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={buttonClass}
        title="Reddit"
      >
        <RedditLogoIcon className="w-4 h-4" />
      </a>
      <button
        onClick={handleCopyLink}
        className={buttonClass}
        title={t('share.copyLink')}
      >
        {copied ? <Check className="w-4 h-4 text-green-400" /> : <Link2 className="w-4 h-4" />}
      </button>
    </div>
  );
}
