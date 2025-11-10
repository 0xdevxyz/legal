'use client';

import { getComplianceScoreColor, getComplianceScoreLabel } from '@/lib/ai-compliance-api';

interface ComplianceProgressProps {
  score: number;
  maxScore?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export default function ComplianceProgress({
  score,
  maxScore = 100,
  size = 'md',
  showLabel = true,
  className = ''
}: ComplianceProgressProps) {
  const percentage = Math.min(Math.round((score / maxScore) * 100), 100);
  const color = getComplianceScoreColor(percentage);
  const label = getComplianceScoreLabel(percentage);
  
  const sizeConfig = {
    sm: { ring: 80, stroke: 6, text: 'text-lg' },
    md: { ring: 120, stroke: 8, text: 'text-2xl' },
    lg: { ring: 160, stroke: 10, text: 'text-4xl' },
  };
  
  const { ring, stroke, text } = sizeConfig[size];
  const radius = (ring - stroke) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;
  
  const colorClasses = {
    red: 'stroke-red-500',
    orange: 'stroke-orange-500',
    yellow: 'stroke-yellow-500',
    green: 'stroke-green-500',
    gray: 'stroke-gray-500',
  };
  
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={ring}
        height={ring}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={ring / 2}
          cy={ring / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="none"
          className="text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx={ring / 2}
          cy={ring / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`transition-all duration-1000 ease-out ${
            colorClasses[color as keyof typeof colorClasses]
          }`}
        />
      </svg>
      
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-bold ${text}`}>
          {percentage}%
        </span>
        {showLabel && (
          <span className="text-xs text-gray-400 mt-1">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}

