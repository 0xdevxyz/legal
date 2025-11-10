'use client';

import React, { useState } from 'react';
import { X, Copy, Check, Info, AlertTriangle } from 'lucide-react';
import { FixResult } from '@/types/api';

interface FixModalProps {
  isOpen: boolean;
  onClose: () => void;
  fix: FixResult | null;
  issueTitle: string;
}

export const FixModal: React.FC<FixModalProps> = ({ isOpen, onClose, fix, issueTitle }) => {
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [copiedCode, setCopiedCode] = useState(false);

  if (!isOpen || !fix) return null;

  const toggleStepComplete = (stepIndex: number) => {
    const newCompleted = new Set(completedSteps);
    if (newCompleted.has(stepIndex)) {
      newCompleted.delete(stepIndex);
    } else {
      newCompleted.add(stepIndex);
    }
    setCompletedSteps(newCompleted);
  };

  const handleCopyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } catch (err) {
      // Silent fail
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🤖</span>
            <div>
              <h2 className="text-xl font-bold text-gray-900">KI-generierte Lösung</h2>
              <p className="text-sm text-gray-600 mt-1">{issueTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Steps */}
          {(fix as any).steps && (fix as any).steps.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span>✅</span>
                <span>Schritt-für-Schritt Anleitung</span>
              </h3>
              <div className="space-y-3">
                {(fix as any).steps.map((step: any, index: number) => (
                  <div
                    key={index}
                    className={`flex items-start gap-3 p-4 rounded-lg border transition-all ${
                      completedSteps.has(index) 
                        ? 'bg-green-50 border-green-300' 
                        : 'bg-white border-gray-200'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={completedSteps.has(index)}
                      onChange={() => toggleStepComplete(index)}
                      className="mt-1 w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-800 mb-1">
                        {index + 1}. {typeof step === 'string' ? step : step.title}
                      </div>
                      {typeof step === 'object' && step.description && (
                        <p className="text-gray-600 text-sm">{step.description}</p>
                      )}
                      {typeof step === 'object' && step.visual_hint && (
                        <p className="text-blue-600 text-sm mt-1">💡 {step.visual_hint}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Code */}
          {(fix as any).code && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                  <span>💻</span>
                  <span>Code zum Kopieren</span>
                </h3>
                <button
                  onClick={() => handleCopyCode((fix as any).code)}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  {copiedCode ? (
                    <>
                      <Check className="w-4 h-4" />
                      Kopiert!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Kopieren
                    </>
                  )}
                </button>
              </div>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                <code>{(fix as any).code}</code>
              </pre>
            </div>
          )}

          {/* Placement */}
          {(fix as any).placement && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-gray-800 mb-1">📍 Wo einfügen</div>
                  <p className="text-gray-700 text-sm">{(fix as any).placement}</p>
                </div>
              </div>
            </div>
          )}

          {/* Transparency Note */}
          {(fix as any).transparency_note && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-gray-800 mb-1">ℹ️ Wichtiger Hinweis</div>
                  <p className="text-gray-700 text-sm">{(fix as any).transparency_note}</p>
                </div>
              </div>
            </div>
          )}

          {/* Meta Info */}
          <div className="flex items-center gap-6 text-sm text-gray-600 pt-4 border-t">
            {(fix as any).estimated_time && (
              <div className="flex items-center gap-2">
                <span>⏱️</span>
                <span className="font-medium">{(fix as any).estimated_time}</span>
              </div>
            )}
            {(fix as any).difficulty && (
              <div className="flex items-center gap-2">
                <span>📊</span>
                <span className="font-medium">{(fix as any).difficulty}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="w-full bg-gray-900 hover:bg-gray-800 text-white py-3 rounded-lg font-semibold transition-colors"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );
};

