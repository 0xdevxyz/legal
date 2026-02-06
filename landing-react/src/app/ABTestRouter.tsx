'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ComplyoOriginalLanding from '../components/ComplyoOriginalLanding';
import ComplyoHighConversionLanding from '../components/ComplyoHighConversionLanding';
import ProfessionalLanding from '../components/ProfessionalLanding';
import ComplyoModernLanding from '../components/ComplyoModernLanding';
import ComplyoViralLanding from '../components/ComplyoViralLanding';
import AlfimaLanding from '../components/AlfimaLanding';
import { useABTestTracking } from '../hooks/useABTestTracking';

type Variant = 'professional' | 'original' | 'high-conversion' | 'modern' | 'viral' | 'alfima';

function ABTestContent() {
  const [variant, setVariant] = useState<Variant | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const searchParams = useSearchParams();
  const { trackVariantAssignment } = useABTestTracking();

  useEffect(() => {
    const initializeABTest = async () => {
      try {
        const forceVariant = searchParams.get('variant');

        // Force-Modus: Nutzer kann Variante per URL-Parameter wählen
        if (forceVariant === 'professional' || forceVariant === 'original' || forceVariant === 'high-conversion' || forceVariant === 'modern' || forceVariant === 'viral' || forceVariant === 'alfima') {
          console.log(`🔧 Force-Modus: ${forceVariant}`);
          setVariant(forceVariant);
          const sessionId = await trackVariantAssignment(forceVariant, 'forced');
          setSessionId(sessionId);
        } else {
          const storedVariant = localStorage.getItem('complyo_ab_variant');
          const storedSessionId = localStorage.getItem('complyo_session_id');

          // Returning User: Zeige gespeicherte Variante
          if (storedVariant && storedSessionId &&
              (storedVariant === 'professional' || storedVariant === 'original' || storedVariant === 'high-conversion' || storedVariant === 'modern' || storedVariant === 'viral' || storedVariant === 'alfima')) {
            console.log(`🔄 Returning User: ${storedVariant}`);
            setVariant(storedVariant as Variant);
            setSessionId(storedSessionId);
          } else {
            // New User: Gewichtete Zufallsauswahl
            // 67% Professional, 17% Original, 16% High-Conversion
            const random = Math.random();
            let randomVariant: Variant;
            
            if (random < 0.67) {
              randomVariant = 'professional'; // 67% (2/3)
            } else if (random < 0.84) {
              randomVariant = 'original'; // 17% (1/6)
            } else {
              randomVariant = 'high-conversion'; // 16% (1/6)
            }
            
            console.log(`🎲 New User Assignment: ${randomVariant} (random: ${random.toFixed(3)})`);
            setVariant(randomVariant);

            const newSessionId = await trackVariantAssignment(randomVariant, 'new');
            setSessionId(newSessionId);

            localStorage.setItem('complyo_ab_variant', randomVariant);
            localStorage.setItem('complyo_session_id', newSessionId);
          }
        }
      } catch (error) {
        console.error('A/B Test Initialization Error:', error);
        setVariant('professional'); // Fallback zur besten Variante
        setSessionId('fallback-session');
      } finally {
        setIsLoading(false);
      }
    };

    initializeABTest();
  }, [searchParams, trackVariantAssignment]);

  if (isLoading || !variant) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <div className="text-white text-lg font-semibold">Lade Complyo...</div>
          <div className="text-gray-400 text-sm mt-2">Initialisiere A/B Test</div>
        </div>
      </div>
    );
  }

  // Render entsprechende Variante
  if (variant === 'alfima') {
    return <AlfimaLanding />;
  } else if (variant === 'viral') {
    return <ComplyoViralLanding />;
  } else if (variant === 'modern') {
    return <ComplyoModernLanding />;
  } else if (variant === 'professional') {
    return <ProfessionalLanding />;
  } else if (variant === 'original') {
    const commonProps = { variant: 'original' as const, sessionId };
    return <ComplyoOriginalLanding {...commonProps} />;
  } else {
    const commonProps = { variant: 'high-conversion' as const, sessionId };
    return <ComplyoHighConversionLanding {...commonProps} />;
  }
}

export default function ABTestRouter() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <div className="text-white text-lg font-semibold">Lade Complyo...</div>
          <div className="text-gray-400 text-sm mt-2">Initialisiere A/B Test</div>
        </div>
      </div>
    }>
      <ABTestContent />
    </Suspense>
  );
}
