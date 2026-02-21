import { useState } from 'react';
import { getInitials } from '@/lib/utils';

interface Props {
  src?: string | null;
  name: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-12 h-12 text-sm',
  lg: 'w-20 h-20 text-xl',
};

// Pixel dimensions for width/height attributes (prevents CLS)
const sizePx = { sm: 32, md: 48, lg: 80 };

function Fallback({ name, size = 'md' }: { name: string; size?: string }) {
  return (
    <div
      className={`${sizeMap[size as keyof typeof sizeMap] || sizeMap.md} rounded-full bg-purple-600 flex items-center justify-center font-semibold`}
    >
      {getInitials(name)}
    </div>
  );
}

/** Derive thumbnail URL from full avatar URL (convention: _thumb before .webp) */
function getThumbUrl(url: string): string {
  if (url.includes('/api/uploads/') && url.endsWith('.webp')) {
    return url.replace('.webp', '_thumb.webp');
  }
  return url;
}

export function Avatar({ src, name, size = 'md' }: Props) {
  const safeSrc = src && (/^https?:\/\//.test(src) || src.startsWith('/api/uploads/')) ? src : null;
  const [errored, setErrored] = useState(false);
  const [thumbErrored, setThumbErrored] = useState(false);

  if (safeSrc && !errored) {
    const displaySrc = thumbErrored ? safeSrc : getThumbUrl(safeSrc);
    return (
      <img
        src={displaySrc}
        alt={name}
        width={sizePx[size]}
        height={sizePx[size]}
        loading="lazy"
        decoding="async"
        onError={() => {
          if (!thumbErrored && displaySrc !== safeSrc) {
            setThumbErrored(true);
          } else {
            setErrored(true);
          }
        }}
        className={`${sizeMap[size]} rounded-full object-cover`}
      />
    );
  }
  return <Fallback name={name} size={size} />;
}
