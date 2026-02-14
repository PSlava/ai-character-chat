import { useTranslation } from 'react-i18next';
import { Link2, Check, Share2 } from 'lucide-react';
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

function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
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
  const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(`${shareText}\n${url}`)}`;
  const redditUrl = `https://reddit.com/submit?url=${encodedUrl}&title=${encodedText}`;

  const canNativeShare = typeof navigator !== 'undefined' && !!navigator.share;

  const handleNativeShare = async () => {
    try {
      await navigator.share({ title: name, text: shareText, url });
    } catch {
      // User cancelled — ignore
    }
  };

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
      {canNativeShare && (
        <button
          onClick={handleNativeShare}
          className={buttonClass}
          title={t('share.label')}
        >
          <Share2 className="w-4 h-4" />
        </button>
      )}
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
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={buttonClass}
        title="WhatsApp"
      >
        <WhatsAppIcon className="w-4 h-4" />
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
