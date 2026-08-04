import React from 'react';
import Image from 'next/image';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  variant?: 'default' | 'light' | 'dark';
  className?: string;
  onClick?: () => void;
}

const sizeConfig = {
  sm: {
    width: 120,
    height: 40,
  },
  md: {
    width: 160,
    height: 54,
  },
  lg: {
    width: 220,
    height: 74,
  },
  xl: {
    width: 280,
    height: 94,
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
  
  // Wähle das richtige Logo basierend auf Variante
  // light = heller Hintergrund -> logo-dark.png (dunkler Text)
  // dark/default = dunkler Hintergrund -> logo-light.png (heller Text)
  const logoSrc = variant === 'light' 
    ? '/logo-dark-trim.png'   // Dunkles Logo für hellen Hintergrund
    : '/logo-light-trim.png'; // Helles Logo für dunklen Hintergrund (default)

  return (
    <div 
      className={`flex items-center group ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      <Image
        src={logoSrc}
        alt="Complyo Logo"
        width={config.width}
        height={config.height}
        className="group-hover:opacity-90 transition-opacity duration-300"
        priority
      />
    </div>
  );
};

export default Logo;

