import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'critical' | 'warning' | 'success' | 'info' | 'outline' | 'secondary' | 'default';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'info', 
  className 
}) => {
  const variants: Record<string, string> = {
    critical: 'bg-red-500/15 border-red-500/30 text-red-400 shadow-sm shadow-red-500/10',
    warning: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-400 shadow-sm shadow-yellow-500/10',
    success: 'bg-green-500/15 border-green-500/30 text-green-400 shadow-sm shadow-green-500/10',
    info: 'bg-sky-500/15 border-sky-500/30 text-sky-400 shadow-sm shadow-sky-500/10',
    outline: 'dark:bg-zinc-900/50 bg-gray-50 dark:border-zinc-700 border-gray-200 text-zinc-300 shadow-sm',
    secondary: 'dark:bg-zinc-700/50 bg-gray-100 dark:border-zinc-600 border-gray-300 text-zinc-300 shadow-sm',
    default: 'dark:bg-zinc-800/50 bg-gray-50 dark:border-zinc-700 border-gray-200 text-zinc-400 shadow-sm',
  };

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold border backdrop-blur-sm transition-all',
      variants[variant],
      className
    )}>
      {children}
    </span>
  );
};
