interface Props {
  className?: string;
}

export function Logo({ className = 'w-6 h-6' }: Props) {
  return (
    <img
      src="/logo.png"
      alt="GrimQuill"
      className={className}
      draggable={false}
    />
  );
}
