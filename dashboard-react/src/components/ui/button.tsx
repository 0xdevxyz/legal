import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: React.ReactNode;
  as?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'default',
  size = 'md',
  isLoading = false,
  className,
  children,
  disabled,
  as: _as,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-300 ease-out focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-40 disabled:cursor-not-allowed active:scale-95';
  
  const variants = {
    default: 'bg-gradient-to-r from-sky-500 to-purple-500 hover:from-sky-600 hover:to-purple-600 text-white shadow-lg shadow-sky-500/20 hover:shadow-xl hover:shadow-sky-500/30 focus:ring-sky-500 focus:ring-offset-zinc-900 dark:focus:ring-offset-zinc-900',
    secondary: 'bg-gray-200 dark:bg-zinc-800 hover:bg-gray-300 dark:hover:bg-zinc-700 text-gray-900 dark:text-white border border-gray-300 dark:border-zinc-700 hover:border-gray-400 dark:hover:border-zinc-600 shadow-md dark:shadow-md focus:ring-gray-500 dark:focus:ring-zinc-600 focus:ring-offset-white dark:focus:ring-offset-zinc-900',
    outline: 'border-2 border-gray-300 dark:border-zinc-700 hover:border-gray-400 dark:hover:border-zinc-600 hover:bg-gray-100 dark:hover:bg-zinc-800/50 text-gray-700 dark:text-zinc-300 hover:text-gray-900 dark:hover:text-white focus:ring-gray-500 dark:focus:ring-zinc-600 focus:ring-offset-white dark:focus:ring-offset-zinc-900',
    ghost: 'hover:bg-gray-100 dark:hover:bg-zinc-800/50 text-gray-700 dark:text-zinc-300 hover:text-gray-900 dark:hover:text-white focus:ring-gray-500 dark:focus:ring-zinc-600 focus:ring-offset-white dark:focus:ring-offset-zinc-900',
    destructive: 'bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/20 hover:shadow-xl hover:shadow-red-500/30 focus:ring-red-500 focus:ring-offset-zinc-900 dark:focus:ring-offset-zinc-900'
  };
  
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-8 py-4 text-base'
  };

  return (
    <button
      className={cn(baseClasses, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
};
