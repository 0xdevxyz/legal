'use client';

import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { ClientOnlyPortal } from '@/components/ClientOnlyPortal';
import { LegalDocumentGenerator, type WizardDocType } from './LegalDocumentGenerator';

interface LegalWizardModalProps {
  documentType: WizardDocType;
  onClose: () => void;
  onComplete: (data: any) => void;
}

/**
 * Overlay für den Rechtstexte-Assistenten.
 *
 * Das Overlay muss per Portal an <body> hängen: die Issue-Karten stecken in
 * einem Container mit `glass-card` (backdrop-filter) und `overflow-hidden`.
 * Ein backdrop-filter macht den Container zum Bezugsrahmen für `position: fixed`
 * — das Overlay wurde dadurch auf die Kartenbreite eingesperrt und
 * abgeschnitten, sichtbar blieb nur der Kopf des Assistenten.
 */
export const LegalWizardModal: React.FC<LegalWizardModalProps> = ({
  documentType,
  onClose,
  onComplete,
}) => {
  // Hintergrund festhalten, solange das Overlay offen ist, und Escape schließt.
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [onClose]);

  return (
    <ClientOnlyPortal>
      <div
        className="fixed inset-0 z-[100] overflow-y-auto overscroll-contain"
        role="dialog"
        aria-modal="true"
      >
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal Content */}
        <div className="relative min-h-full flex items-start justify-center p-4 py-10">
          <div className="relative w-full max-w-4xl dark:bg-zinc-950 bg-white rounded-2xl shadow-2xl border dark:border-zinc-800 border-gray-200">
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-gray-600 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-lg transition-colors z-10"
              aria-label="Schließen"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="p-6">
              <LegalDocumentGenerator
                documentType={documentType}
                onComplete={onComplete}
                onBack={onClose}
              />
            </div>
          </div>
        </div>
      </div>
    </ClientOnlyPortal>
  );
};

export default LegalWizardModal;
