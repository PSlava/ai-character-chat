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
      {/* Open book — left page */}
      <path
        d="M32 18C26 14 18 13 8 15V48C18 46 26 47 32 51Z"
        fill="currentColor"
        opacity="0.6"
      />
      {/* Open book — right page */}
      <path
        d="M32 18C38 14 46 13 56 15V48C46 46 38 47 32 51Z"
        fill="currentColor"
        opacity="0.85"
      />
      {/* Spine highlight */}
      <path
        d="M32 18V51"
        stroke="currentColor"
        strokeWidth="1.5"
        opacity="0.4"
      />
      {/* Text lines on left page */}
      <line x1="14" y1="24" x2="28" y2="26" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
      <line x1="14" y1="30" x2="26" y2="31" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
      <line x1="14" y1="36" x2="27" y2="36" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
      {/* Text lines on right page */}
      <line x1="36" y1="26" x2="50" y2="24" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
      <line x1="36" y1="31" x2="50" y2="30" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
      <line x1="36" y1="36" x2="49" y2="36" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.3" />
      {/* Magic star/spark above the book */}
      <path
        d="M32 4L34 9L39 9L35 12L36.5 17L32 14L27.5 17L29 12L25 9L30 9Z"
        fill="currentColor"
      />
    </svg>
  );
}
