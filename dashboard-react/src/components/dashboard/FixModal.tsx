'use client';

import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { FixResult } from '@/types/api';
import { AIFixDisplay } from '@/components/ai/AIFixDisplay';
import { ClientOnlyPortal } from '../ClientOnlyPortal';

interface FixModalProps {
  isOpen: boolean;
  onClose: () => void;
  fix: FixResult | null;
  issueTitle: string;
}

export const FixModal: React.FC<FixModalProps> = ({ isOpen, onClose, fix, issueTitle }) => {
  // ✅ CRITICAL: SSR-Check ZUERST
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // ✅ CRITICAL: EARLY RETURN für SSR - BEVOR irgendetwas anderes passiert!
  if (!mounted || typeof document === 'undefined') return null;
  if (!isOpen || !fix) return null;

  // Transform old fix format to new AIFixDisplay format
  const transformedFix = {
    fix_id: (fix as any).id || 'generated-fix',
    fix_type: (fix as any).type || ((fix as any).steps ? 'guide' : (fix as any).code ? 'code' : 'text'),
    title: issueTitle,
    description: (fix as any).description || 'KI-generierte Lösung für dieses Problem',
    
    // Code Fix
    code: (fix as any).code,
    language: (fix as any).language || 'html',
    
    // Guide Fix
    steps: (fix as any).steps,
    difficulty: (fix as any).difficulty,
    
    // Common
    integration: {
      instructions: (fix as any).placement,
      where: (fix as any).placement
    },
    estimated_time: (fix as any).estimated_time,
    metadata: {
      transparency_note: (fix as any).transparency_note
    }
  };

  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 overflow-y-auto">
      <div className="relative w-full max-w-5xl my-8">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 text-gray-400 hover:text-gray-600 transition-colors bg-white rounded-full p-2 shadow-lg"
          aria-label="Schließen"
        >
          <X className="w-6 h-6" />
        </button>

        {/* New AIFixDisplay Component */}
        <AIFixDisplay
          fixData={transformedFix as any}
          onFeedback={(rating, feedback) => {
            console.log('User feedback:', { rating, feedback });
            // TODO: Send feedback to backend
            // fetch('/api/v2/feedback', { ... })
          }}
          onApply={() => {
            console.log('Fix applied');
            onClose();
          }}
        />

        {/* Close Button at Bottom */}
        <div className="mt-4 flex justify-center">
          <button
            onClick={onClose}
            className="bg-gray-900 hover:bg-gray-800 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );

  // ✅ 100% SSR-SAFE mit ClientOnlyPortal
  return <ClientOnlyPortal>{modalContent}</ClientOnlyPortal>;
};
