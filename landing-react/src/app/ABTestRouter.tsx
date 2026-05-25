'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ComplyoOriginalLanding from '../components/ComplyoOriginalLanding';
import ComplyoHighConversionLanding from '../components/ComplyoHighConversionLanding';
import ProfessionalLanding from '../components/ProfessionalLanding';
import ComplyoModernLanding from '../components/ComplyoModernLanding';
import ComplyoViralLanding from '../components/ComplyoViralLanding';
import AlfimaLanding from '../components/AlfimaLanding';
import SaasLanding from '../components/saas-landing/SaasLanding';
import { useABTestTracking } from '../hooks/useABTestTracking';

type Variant = 'professional' | 'original' | 'high-conversion' | 'modern' | 'viral' | 'alfima' | 'saas';

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

        const validVariants: Variant[] = ['professional', 'original', 'high-conversion', 'modern', 'viral', 'alfima', 'saas'];

        if (forceVariant && validVariants.includes(forceVariant as Variant)) {
          console.log(`🔧 Force-Modus: ${forceVariant}`);
          setVariant(forceVariant as Variant);
          const sid = await trackVariantAssignment(forceVariant as Variant, 'forced');
          setSessionId(sid);
        } else {
          const storedVariant = localStorage.getItem('complyo_ab_variant');
          const storedSessionId = localStorage.getItem('complyo_session_id');

          if (storedVariant && storedSessionId && validVariants.includes(storedVariant as Variant)) {
            console.log(`🔄 Returning User: ${storedVariant}`);
            setVariant(storedVariant as Variant);
            setSessionId(storedSessionId);
          } else {
            const random = Math.random();
            let randomVariant: Variant;

            if (random < 0.67) {
              randomVariant = 'saas'; // Neue Standard-Variante
            } else if (random < 0.84) {
              randomVariant = 'professional';
            } else {
              randomVariant = 'high-conversion';
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
        setVariant('saas');
        setSessionId('fallback-session');
      } finally {
        setIsLoading(false);
      }
    };

    initializeABTest();
  }, [searchParams, trackVariantAssignment]);

  if (isLoading || !variant) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-700 text-base font-semibold">Lade Complyo...</div>
        </div>
      </div>
    );
  }

  if (variant === 'saas') return <SaasLanding />;
  if (variant === 'alfima') return <AlfimaLanding />;
  if (variant === 'viral') return <ComplyoViralLanding />;
  if (variant === 'modern') return <ComplyoModernLanding />;
  if (variant === 'professional') return <ProfessionalLanding />;
  if (variant === 'original') {
    return <ComplyoOriginalLanding variant="original" sessionId={sessionId} />;
  }
  return <ComplyoHighConversionLanding variant="high-conversion" sessionId={sessionId} />;
}

export default function ABTestRouter() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-700 text-base font-semibold">Lade Complyo...</div>
        </div>
      </div>
    }>
      <ABTestContent />
    </Suspense>
  );
}
