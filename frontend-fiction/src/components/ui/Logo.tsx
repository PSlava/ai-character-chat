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
      {/* Magic star/spark above the book */}
      <path
        d="M32 4L34 9L39 9L35 12L36.5 17L32 14L27.5 17L29 12L25 9L30 9Z"
        fill="currentColor"
      />
    </svg>
  );
}
