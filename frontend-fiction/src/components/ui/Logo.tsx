interface Props {
  className?: string;
}

export function Logo({ className = 'w-6 h-6' }: Props) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Quill pen */}
      <path
        d="M20 48L28 28L44 12C48 8 54 10 52 16L36 32L20 48Z"
        fill="currentColor"
        opacity="0.9"
      />
      <path
        d="M20 48L28 28L30 30L22 48Z"
        fill="currentColor"
        opacity="0.6"
      />
      {/* Branching paths */}
      <path
        d="M36 32Q42 36 48 32"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.7"
      />
      <path
        d="M36 32Q40 40 44 44"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.7"
      />
      <path
        d="M36 32Q34 40 30 44"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.7"
      />
      {/* Choice dots */}
      <circle cx="48" cy="32" r="2.5" fill="currentColor" opacity="0.8" />
      <circle cx="44" cy="44" r="2.5" fill="currentColor" opacity="0.8" />
      <circle cx="30" cy="44" r="2.5" fill="currentColor" opacity="0.8" />
    </svg>
  );
}
