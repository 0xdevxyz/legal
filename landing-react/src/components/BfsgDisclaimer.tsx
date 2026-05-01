'use client';
import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function BfsgDisclaimer() {
  return (
    <div
      role="alert"
      className="bg-amber-500/10 border border-amber-400/40 rounded-xl px-5 py-4 flex items-start gap-3 max-w-7xl mx-auto my-4"
      data-testid="bfsg-disclaimer"
    >
      <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div>
        <p className="text-sm font-semibold text-amber-300">
          BFSG-Deadline war der 28. Juni 2025
        </p>
        <p className="text-sm text-gray-300 mt-1">
          Die gesetzliche Frist ist abgelaufen. Complyo hilft Ihnen ab jetzt, BFSG-konform zu werden
          (Forward-Looking Compliance) — keine Retroaktiv-Zertifizierung fuer vergangene Zeitraeume moeglich.
        </p>
      </div>
    </div>
  );
}
