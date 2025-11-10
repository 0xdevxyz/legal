'use client';

import ABTestRouter from './ABTestRouter';

// Force dynamic rendering to support URL parameters
export const dynamic = 'force-dynamic';

/**
 * Landing-Page mit A/B-Test Router (3 Varianten)
 * Zeigt verschiedene Landing-Varianten basierend auf ?variant= Parameter
 * 
 * URLs:
 * - / → Gewichteter A/B-Test: 67% Professional, 17% Original, 16% High-Conversion
 * - /?variant=professional → ProfessionalLanding (Eye-Able®-Stil, modular, beste UX)
 * - /?variant=original → ComplyoOriginalLanding (klassisch)
 * - /?variant=high-conversion → ComplyoHighConversionLanding (Sales-fokussiert)
 */
export default function Page() {
  return <ABTestRouter />;
}
