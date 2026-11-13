import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || props.name;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-medium text-slate-300 mb-1.5">
          {label}
        </label>
      )}
      <div className="relative rounded-lg">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          className={`w-full bg-slate-900/80 border ${error ? 'border-red-500/80 focus:ring-red-500' : 'border-slate-800 focus:border-brand-500/80 focus:ring-brand-500/20'} rounded-lg py-2 ${leftIcon ? 'pl-10' : 'pl-3.5'} pr-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 transition-colors ${className}`}
          {...props}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
      {helperText && !error && <p className="mt-1 text-xs text-slate-400">{helperText}</p>}
    </div>
  );
};
