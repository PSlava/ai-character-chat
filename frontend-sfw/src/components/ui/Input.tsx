import { InputHTMLAttributes, TextareaHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hideCount?: boolean;
}

export function Input({ label, className = '', hideCount, ...props }: InputProps) {
  const len = typeof props.value === 'string' ? props.value.length : 0;
  const max = props.maxLength;
  const showCount = !hideCount && max && max > 0;

  return (
    <div>
      {label && (
        <label className="block text-sm text-neutral-400 mb-1">{label}</label>
      )}
      <input
        className={`w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white placeholder-neutral-500 focus:outline-none focus:border-blue-500 ${className}`}
        {...props}
      />
      {showCount && (
        <div className={`text-xs mt-1 text-right ${len > max * 0.9 ? 'text-amber-400' : 'text-neutral-600'}`}>
          {len}/{max}
        </div>
      )}
    </div>
  );
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hideCount?: boolean;
  hint?: string;
}

export function Textarea({ label, className = '', hideCount, hint, ...props }: TextareaProps) {
  const len = typeof props.value === 'string' ? props.value.length : 0;
  const max = props.maxLength;
  const showCount = !hideCount && max && max > 0;

  return (
    <div>
      {label && (
        <label className="block text-sm text-neutral-400 mb-1">{label}</label>
      )}
      {hint && (
        <p className="text-xs text-neutral-500 mb-1">{hint}</p>
      )}
      <textarea
        className={`w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white placeholder-neutral-500 focus:outline-none focus:border-blue-500 resize-none ${className}`}
        {...props}
      />
      {showCount && (
        <div className={`text-xs mt-1 text-right ${len > max * 0.9 ? 'text-amber-400' : 'text-neutral-600'}`}>
          {len}/{max}
        </div>
      )}
    </div>
  );
}
