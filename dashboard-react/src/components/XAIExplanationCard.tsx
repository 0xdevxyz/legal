'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, Scale, Sparkles } from 'lucide-react';

export interface NormReferenceType {
  law: string;
  article: string;
  paragraph?: string;
  url?: string;
  relevance_score?: number;
  quote?: string;
}

export interface FactorType {
  factor: string;
  weight: number;
  description: string;
}

export interface ExplanationDocType {
  cited_norms: NormReferenceType[];
  triggering_factors: FactorType[];
  confidence_breakdown: Record<string, number>;
  counterfactuals: string[];
  xai_version?: string;
}

interface XAIExplanationCardProps {
  explanation: ExplanationDocType;
  reasoning: string;
  confidence: number;
}

const breakdownColors: Record<string, string> = {
  law_match_score: 'bg-blue-500',
  severity_keywords: 'bg-red-500',
  historical_precedent: 'bg-purple-500',
  context_clarity: 'bg-emerald-500',
};

const breakdownLabels: Record<string, string> = {
  law_match_score: 'Norm-Match',
  severity_keywords: 'Severity',
  historical_precedent: 'Präzedenz',
  context_clarity: 'Kontext',
};

const formatPercent = (value: number) => `${Math.round(Math.max(0, Math.min(value, 1)) * 100)}%`;

export const XAIExplanationCard: React.FC<XAIExplanationCardProps> = ({
  explanation,
  reasoning,
  confidence,
}) => {
  const [counterfactualsOpen, setCounterfactualsOpen] = useState(false);
  const breakdownEntries = Object.entries(explanation.confidence_breakdown || {});
  const totalBreakdown = breakdownEntries.reduce((sum, [, value]) => sum + Math.max(value, 0), 0) || 1;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-md">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-blue-700">
            <Sparkles className="h-4 w-4" />
            Explainable AI
          </div>
          <h3 className="mt-1 text-lg font-bold text-gray-900">Warum diese Compliance-Einschätzung?</h3>
        </div>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-700">
          {formatPercent(confidence)} Konfidenz
        </span>
      </div>

      <p className="mb-5 text-sm leading-relaxed text-gray-700">{reasoning}</p>

      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between text-xs font-medium text-gray-500">
          <span>Confidence Breakdown</span>
          <span>{formatPercent(confidence)}</span>
        </div>
        <div className="flex h-3 overflow-hidden rounded-full bg-gray-100">
          {breakdownEntries.map(([key, value]) => (
            <div
              key={key}
              className={`${breakdownColors[key] || 'bg-gray-400'} h-full`}
              style={{ width: `${(Math.max(value, 0) / totalBreakdown) * 100}%` }}
              title={`${breakdownLabels[key] || key}: ${formatPercent(value)}`}
            />
          ))}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {breakdownEntries.map(([key, value]) => (
            <div key={key} className="flex items-center gap-2 text-xs text-gray-600">
              <span className={`h-2.5 w-2.5 rounded-full ${breakdownColors[key] || 'bg-gray-400'}`} />
              <span>{breakdownLabels[key] || key}: {formatPercent(value)}</span>
            </div>
          ))}
        </div>
      </div>

      {explanation.cited_norms?.length > 0 && (
        <div className="mb-6">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-800">
            <Scale className="h-4 w-4 text-blue-600" />
            Zitierte Normen
          </div>
          <div className="flex flex-wrap gap-2">
            {explanation.cited_norms.map((norm, index) => {
              const label = [norm.law, norm.article, norm.paragraph].filter(Boolean).join(' ');
              return norm.url ? (
                <a
                  key={`${label}-${index}`}
                  href={norm.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 transition hover:bg-blue-100"
                >
                  {label}
                  <ExternalLink className="h-3 w-3" />
                </a>
              ) : (
                <span
                  key={`${label}-${index}`}
                  className="inline-flex items-center rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-sm font-medium text-gray-700"
                >
                  {label}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {explanation.triggering_factors?.length > 0 && (
        <div className="mb-6">
          <h4 className="mb-3 text-sm font-semibold text-gray-800">Auslösende Faktoren</h4>
          <div className="space-y-3">
            {explanation.triggering_factors.map((factor) => (
              <div key={factor.factor}>
                <div className="mb-1 flex justify-between gap-3 text-xs text-gray-600">
                  <span className="font-medium text-gray-800">{factor.factor}</span>
                  <span>{formatPercent(factor.weight)}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                  <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-emerald-500" style={{ width: formatPercent(factor.weight) }} />
                </div>
                <p className="mt-1 text-xs text-gray-500">{factor.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-gray-200 bg-gray-50">
        <button
          type="button"
          onClick={() => setCounterfactualsOpen((open) => !open)}
          className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-800"
        >
          Counterfactuals
          {counterfactualsOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {counterfactualsOpen && (
          <div className="space-y-2 border-t border-gray-200 px-4 py-3">
            {explanation.counterfactuals?.length > 0 ? (
              explanation.counterfactuals.map((item, index) => (
                <p key={index} className="rounded-lg bg-white p-3 text-sm text-gray-700 shadow-sm">
                  {item}
                </p>
              ))
            ) : (
              <p className="text-sm text-gray-500">Keine Counterfactual-Erklärungen verfügbar.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default XAIExplanationCard;
