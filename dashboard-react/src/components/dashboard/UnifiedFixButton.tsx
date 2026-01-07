'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface UnifiedFixButtonProps {
  issueTitle?: string;
  isGroup?: boolean;
  onFix: () => void;
  disabled?: boolean;
  isLoading?: boolean;
  className?: string;
}

export const UnifiedFixButton: React.FC<UnifiedFixButtonProps> = ({
  issueTitle,
  isGroup = false,
  onFix,
  disabled = false,
  isLoading = false,
  className = ''
}) => {
  const buttonText = isGroup 
    ? 'Alle Probleme beheben' 
    : 'Problem beheben';

  return (
    <button
      onClick={onFix}
      disabled={disabled || isLoading}
      className={`
        flex items-center justify-center gap-2 
        px-5 py-3 
        bg-gradient-to-r from-blue-600 to-purple-600 
        hover:from-blue-700 hover:to-purple-700 
        text-white rounded-lg font-semibold 
        shadow-lg hover:shadow-xl 
        transition-all duration-200 
        disabled:opacity-50 disabled:cursor-not-allowed
        ${isGroup ? 'w-full' : ''}
        ${className}
      `}
      aria-label={issueTitle ? `${buttonText}: ${issueTitle}` : buttonText}
    >
      {isLoading ? (
        <>
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          <span>Wird behoben...</span>
        </>
      ) : (
        <>
          <Sparkles className="w-5 h-5" />
          <span>{buttonText}</span>
        </>
      )}
    </button>
  );
};

