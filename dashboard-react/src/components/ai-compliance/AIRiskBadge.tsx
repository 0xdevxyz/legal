'use client';

import { getRiskCategoryColor, getRiskCategoryLabel } from '@/lib/ai-compliance-api';
import type { RiskCategory } from '@/types/ai-compliance';

interface AIRiskBadgeProps {
  category: RiskCategory;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function AIRiskBadge({
  category,
  showLabel = true,
  size = 'md',
  className = ''
}: AIRiskBadgeProps) {
  const color = getRiskCategoryColor(category);
  const label = getRiskCategoryLabel(category);
  
  const colorClasses = {
    red: 'bg-red-500/20 text-red-400 border-red-500/30',
    orange: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    green: 'bg-green-500/20 text-green-400 border-green-500/30',
    gray: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };
  
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full border font-medium
        ${colorClasses[color as keyof typeof colorClasses]}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      <span className={`w-2 h-2 rounded-full bg-current animate-pulse`} />
      {showLabel && label}
    </span>
  );
}

