'use client';

import React from 'react';
import Image from 'next/image';
import { useTheme } from '@/contexts/ThemeContext';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  /**
   * 'auto' (Standard) folgt dem aktiven Theme. 'light'/'dark' beschreiben den
   * HINTERGRUND, auf dem das Logo sitzt — nur setzen, wenn der Hintergrund
   * unabhaengig vom Theme fest ist (z. B. Login-Panel).
   */
  variant?: 'auto' | 'default' | 'light' | 'dark';
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
  variant = 'auto',
  className = '',
  onClick
}) => {
  const config = sizeConfig[size];
  const { theme } = useTheme();

  // Das Logo folgt standardmaessig dem Theme. Vorher stand hier fest die
  // helle Variante — im hellen Design war das weisse Logo damit unsichtbar.
  // light/dark beschreiben den Hintergrund: heller Hintergrund braucht das
  // dunkle Logo und umgekehrt.
  const hintergrundHell = variant === 'auto' ? theme === 'light' : variant === 'light';
  const logoSrc = hintergrundHell
    ? '/logo-dark-trim.png'   // Dunkles Logo für hellen Hintergrund
    : '/logo-light-trim.png'; // Helles Logo für dunklen Hintergrund

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

