'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ComplyoOriginalLanding from '../components/ComplyoOriginalLanding';
import ComplyoHighConversionLanding from '../components/ComplyoHighConversionLanding';
import { useABTestTracking } from '../hooks/useABTestTracking';

function ABTestContent() {
  const [variant, setVariant] = useState<'original' | 'high-conversion' | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const searchParams = useSearchParams();
  const { trackVariantAssignment } = useABTestTracking();

  useEffect(() => {
    const initializeABTest = async () => {
      try {
        const forceVariant = searchParams.get('variant');

        if (forceVariant === 'original' || forceVariant === 'high-conversion') {
          console.log(`🔧 Force-Modus: ${forceVariant}`);
          setVariant(forceVariant);
          const sessionId = await trackVariantAssignment(forceVariant, 'forced');
          setSessionId(sessionId);
        } else {
          const storedVariant = localStorage.getItem('complyo_ab_variant');
          const storedSessionId = localStorage.getItem('complyo_session_id');

          if (storedVariant && storedSessionId &&
              (storedVariant === 'original' || storedVariant === 'high-conversion')) {
            console.log(`🔄 Returning User: ${storedVariant}`);
            setVariant(storedVariant as 'original' | 'high-conversion');
            setSessionId(storedSessionId);
          } else {
            const randomVariant = Math.random() < 0.5 ? 'original' : 'high-conversion';
            console.log(`🎲 New User Assignment: ${randomVariant}`);
            setVariant(randomVariant);

            const newSessionId = await trackVariantAssignment(randomVariant, 'new');
            setSessionId(newSessionId);

            localStorage.setItem('complyo_ab_variant', randomVariant);
            localStorage.setItem('complyo_session_id', newSessionId);
          }
        }
      } catch (error) {
        console.error('A/B Test Initialization Error:', error);
        setVariant('original');
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

  const commonProps = { variant, sessionId };

  return variant === 'original'
    ? <ComplyoOriginalLanding {...commonProps} />
    : <ComplyoHighConversionLanding {...commonProps} />;
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
