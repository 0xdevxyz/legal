'use client';

import React from 'react';
import { Sparkles, ArrowRight, Clock, Zap } from 'lucide-react';
import { getQuickTip, explainInSimpleTerms } from '@/lib/ai-explainer';
import type { ComplianceIssue } from '@/types/api';

interface AIFixPreviewProps {
  issue: ComplianceIssue;
  onGenerateFull: () => void;
  className?: string;
}

export const AIFixPreview: React.FC<AIFixPreviewProps> = ({ issue, onGenerateFull, className = '' }) => {
  const explanation = explainInSimpleTerms(issue);
  const quickTip = getQuickTip(issue);

  const urgencyColor = {
    high: 'from-red-500 to-orange-500',
    medium: 'from-yellow-500 to-orange-500',
    low: 'from-blue-500 to-purple-500'
  };

  const urgencyBg = {
    high: 'bg-red-50 border-red-200',
    medium: 'bg-yellow-50 border-yellow-200',
    low: 'bg-blue-50 border-blue-200'
  };

  return (
    <div className={`rounded-lg border-2 ${urgencyBg[explanation.urgency]} p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${urgencyColor[explanation.urgency]} flex items-center justify-center flex-shrink-0`}>
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 mb-1">KI-Vorschlag</h4>
          <p className="text-sm text-gray-700">{explanation.simple}</p>
        </div>
      </div>

      {/* Quick Tip */}
      <div className="bg-white/50 rounded-lg p-3 mb-3">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-semibold text-gray-700">SCHNELLE LÖSUNG</span>
        </div>
        <p className="text-sm text-gray-800 font-medium">{explanation.fix}</p>
      </div>

      {/* Meta Info */}
      <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          <span>{explanation.estimatedTime}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            explanation.urgency === 'high' ? 'bg-red-100 text-red-700' :
            explanation.urgency === 'medium' ? 'bg-yellow-100 text-yellow-700' :
            'bg-blue-100 text-blue-700'
          }`}>
            {explanation.urgency === 'high' ? 'Dringend' :
             explanation.urgency === 'medium' ? 'Wichtig' : 'Optional'}
          </span>
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onGenerateFull}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-2.5 rounded-lg font-semibold text-sm transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        Detaillierten KI-Fix generieren
        <ArrowRight className="w-4 h-4" />
      </button>

      {/* Why Info */}
      <details className="mt-3">
        <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
          Warum ist das wichtig?
        </summary>
        <div className="mt-2 text-xs text-gray-700 space-y-1">
          <p><strong>Rechtslage:</strong> {explanation.why}</p>
          <p><strong>Risiko:</strong> {explanation.risk}</p>
        </div>
      </details>
    </div>
  );
};

/**
 * Inline mini version for subtle hints
 */
export const AIFixPreviewMini: React.FC<{ issue: ComplianceIssue; onClick: () => void }> = ({ issue, onClick }) => {
  const explanation = explainInSimpleTerms(issue);
  
  return (
    <button
      onClick={onClick}
      className="group flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 rounded-lg border border-blue-200 transition-all"
    >
      <Sparkles className="w-4 h-4 text-blue-600" />
      <span className="text-sm text-gray-700 font-medium">
        KI-Fix in {explanation.estimatedTime}
      </span>
      <ArrowRight className="w-4 h-4 text-blue-600 group-hover:translate-x-1 transition-transform" />
    </button>
  );
};

