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
      {/* Devil horns */}
      <path
        d="M16 20L12 4L24 16"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M48 20L52 4L40 16"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Heart */}
      <path
        d="M32 56L8 32C2 24 4 14 14 12C20 10 26 14 32 20C38 14 44 10 50 12C60 14 62 24 56 32L32 56Z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* Devil tail */}
      <path
        d="M32 56C32 56 40 58 46 54C50 51 48 46 44 48C40 50 38 54 32 56Z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="1"
      />
    </svg>
  );
}
