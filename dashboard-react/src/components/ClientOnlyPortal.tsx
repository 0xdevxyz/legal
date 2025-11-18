'use client';

import { useEffect, useState, ReactNode } from 'react';
import { createPortal } from 'react-dom';

/**
 * ClientOnlyPortal - 100% SSR-SAFE Portal Wrapper
 * 
 * Dieser Wrapper garantiert, dass createPortal NUR im Browser aufgerufen wird.
 * KEINE Exceptions mehr während SSR!
 */
interface ClientOnlyPortalProps {
  children: ReactNode;
  selector?: string;
}

export function ClientOnlyPortal({ children, selector = 'body' }: ClientOnlyPortalProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // ✅ GARANTIERT: Kein Rendering während SSR
  if (!mounted || typeof window === 'undefined' || typeof document === 'undefined') {
    return null;
  }

  // ✅ GARANTIERT: document.body existiert
  const container = selector === 'body' 
    ? document.body 
    : document.querySelector(selector);

  if (!container) {
    console.warn(`ClientOnlyPortal: Container "${selector}" not found`);
    return null;
  }

  return createPortal(children, container);
}

