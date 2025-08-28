import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'critical' | 'warning' | 'success' | 'info';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'info', 
  className 
}) => {
  const variants = {
    critical: 'bg-red-900/30 border-red-500/50 text-red-400',
    warning: 'bg-yellow-900/30 border-yellow-500/50 text-yellow-400',
    success: 'bg-green-900/30 border-green-500/50 text-green-400',
    info: 'bg-blue-900/30 border-blue-500/50 text-blue-400'
  };

  return (
    <span className={cn(
      'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border',
      variants[variant],
      className
    )}>
      {children}
    </span>
  );
};
