import React from 'react';
import { Shield } from 'lucide-react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  variant?: 'default' | 'light' | 'dark';
  className?: string;
  onClick?: () => void;
}

const sizeConfig = {
  sm: {
    icon: 'w-4 h-4',
    text: 'text-base',
    padding: 'p-1.5',
    gap: 'gap-1.5'
  },
  md: {
    icon: 'w-5 h-5',
    text: 'text-xl',
    padding: 'p-2',
    gap: 'gap-2'
  },
  lg: {
    icon: 'w-6 h-6',
    text: 'text-2xl',
    padding: 'p-2',
    gap: 'gap-3'
  },
  xl: {
    icon: 'w-8 h-8',
    text: 'text-3xl',
    padding: 'p-3',
    gap: 'gap-4'
  }
};

export const Logo: React.FC<LogoProps> = ({ 
  size = 'md', 
  showText = true, 
  variant = 'default',
  className = '',
  onClick 
}) => {
  const config = sizeConfig[size];
  
  const iconColorClass = variant === 'light' 
    ? 'text-blue-600' 
    : variant === 'dark'
    ? 'text-white'
    : 'text-sky-400';

  const textGradientClass = variant === 'light'
    ? 'bg-gradient-to-r from-blue-600 to-purple-600'
    : 'bg-gradient-to-r from-sky-400 via-blue-400 to-purple-400';

  return (
    <div 
      className={`flex items-center ${config.gap} group ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      <div className="relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-sky-500 to-purple-500 rounded-lg blur opacity-30 group-hover:opacity-50 transition duration-500"></div>
        <div className={`relative bg-zinc-900 ${config.padding} rounded-lg`}>
          <Shield className={`${config.icon} ${iconColorClass} group-hover:scale-110 transition-transform duration-300`} />
        </div>
      </div>
      {showText && (
        <span className={`${config.text} font-bold ${textGradientClass} bg-clip-text text-transparent`}>
          Complyo
        </span>
      )}
    </div>
  );
};

export default Logo;

