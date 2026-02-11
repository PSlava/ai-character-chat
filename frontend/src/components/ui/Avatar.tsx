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

export function Avatar({ src, name, size = 'md' }: Props) {
  const safeSrc = src && (/^https?:\/\//.test(src) || src.startsWith('/api/uploads/')) ? src : null;
  if (safeSrc) {
    return (
      <img
        src={safeSrc}
        alt={name}
        className={`${sizeMap[size]} rounded-full object-cover`}
      />
    );
  }
  return (
    <div
      className={`${sizeMap[size]} rounded-full bg-rose-600 flex items-center justify-center font-semibold`}
    >
      {getInitials(name)}
    </div>
  );
}
