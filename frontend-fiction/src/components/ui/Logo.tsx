interface Props {
  className?: string;
}

export function Logo({ className = 'w-6 h-6' }: Props) {
  return (
    <svg viewBox="0 0 64 68" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <linearGradient id="logo-bg" x1="32" y1="2" x2="32" y2="68" gradientUnits="userSpaceOnUse">
          <stop stopColor="#312e81"/>
          <stop offset="1" stopColor="#1e1b4b"/>
        </linearGradient>
      </defs>
      {/* Background circle with visible gradient */}
      <circle cx="32" cy="35" r="31" fill="url(#logo-bg)" stroke="#4c1d95" strokeWidth="1"/>
      {/* Left page */}
      <path d="M32 22C26 18 18 17 8 19V52C18 50 26 51 32 55Z" fill="#7c3aed"/>
      {/* Right page */}
      <path d="M32 22C38 18 46 17 56 19V52C46 50 38 51 32 55Z" fill="#a78bfa"/>
      {/* Spine */}
      <path d="M32 22V55" stroke="#1e1b4b" strokeWidth="1.5"/>
      {/* Text lines left */}
      <line x1="14" y1="28" x2="28" y2="30" stroke="#1e1b4b" strokeWidth="1.5" strokeLinecap="round" opacity="0.3"/>
      <line x1="14" y1="34" x2="26" y2="35" stroke="#1e1b4b" strokeWidth="1.5" strokeLinecap="round" opacity="0.3"/>
      <line x1="14" y1="40" x2="27" y2="40" stroke="#1e1b4b" strokeWidth="1.5" strokeLinecap="round" opacity="0.3"/>
      {/* Text lines right */}
      <line x1="36" y1="30" x2="50" y2="28" stroke="#1e1b4b" strokeWidth="1.5" strokeLinecap="round" opacity="0.3"/>
      <line x1="36" y1="35" x2="50" y2="34" stroke="#1e1b4b" strokeWidth="1.5" strokeLinecap="round" opacity="0.3"/>
      <line x1="36" y1="40" x2="49" y2="40" stroke="#1e1b4b" strokeWidth="1.5" strokeLinecap="round" opacity="0.3"/>
      {/* Magic star */}
      <path d="M32 6L34.5 12L41 12L36 15.5L37.8 22L32 18L26.2 22L28 15.5L23 12L29.5 12Z" fill="#e9d5ff"/>
    </svg>
  );
}
