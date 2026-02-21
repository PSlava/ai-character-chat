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
      {/* Quill body — solid filled */}
      <path
        d="M18 50L26 30L42 10C47 5 56 8 53 15L35 34L18 50Z"
        fill="currentColor"
      />
      {/* Quill shadow edge */}
      <path
        d="M18 50L26 30L29 33L20 50Z"
        fill="currentColor"
        opacity="0.5"
      />
      {/* Three branch paths — thick filled wedges */}
      <path
        d="M35 34L50 28L49 33L36 36Z"
        fill="currentColor"
        opacity="0.75"
      />
      <path
        d="M35 34L48 46L44 48L34 37Z"
        fill="currentColor"
        opacity="0.75"
      />
      <path
        d="M35 34L28 48L25 45L33 36Z"
        fill="currentColor"
        opacity="0.75"
      />
      {/* Choice dots — solid */}
      <circle cx="51" cy="30" r="3.5" fill="currentColor" />
      <circle cx="49" cy="48" r="3.5" fill="currentColor" />
      <circle cx="26" cy="49" r="3.5" fill="currentColor" />
    </svg>
  );
}
