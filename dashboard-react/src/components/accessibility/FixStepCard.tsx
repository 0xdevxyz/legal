'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Zap,
  Code,
  BookOpen,
  ExternalLink,
  FileCode,
  AlertCircle,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export type FixType = 'widget' | 'code' | 'manual';
export type Difficulty = 'easy' | 'medium' | 'hard';

interface FixStepCardProps {
  title: string;
  description: string;
  difficulty: Difficulty;
  fixType: FixType;
  issuesCount?: number;
  filePath?: string;
  wcagCriteria?: string[];
  codeSnippet?: string;
  steps?: string[];
  resources?: { title: string; url: string }[];
}

// =============================================================================
// Helpers
// =============================================================================

const getDifficultyConfig = (difficulty: Difficulty) => {
  switch (difficulty) {
    case 'easy':
      return {
        label: 'Einfach',
        color: 'green',
        bgClass: 'bg-green-100',
        textClass: 'text-green-700',
        borderClass: 'border-green-200',
      };
    case 'medium':
      return {
        label: 'Mittel',
        color: 'yellow',
        bgClass: 'bg-yellow-100',
        textClass: 'text-yellow-700',
        borderClass: 'border-yellow-200',
      };
    case 'hard':
      return {
        label: 'Komplex',
        color: 'red',
        bgClass: 'bg-red-100',
        textClass: 'text-red-700',
        borderClass: 'border-red-200',
      };
  }
};

const getFixTypeConfig = (fixType: FixType) => {
  switch (fixType) {
    case 'widget':
      return {
        label: 'Widget',
        icon: Zap,
        description: 'Automatisch per Widget',
      };
    case 'code':
      return {
        label: 'Code-Patch',
        icon: Code,
        description: 'Code-Änderung erforderlich',
      };
    case 'manual':
      return {
        label: 'Anleitung',
        icon: BookOpen,
        description: 'Manuelle Schritte',
      };
  }
};

// =============================================================================
// Component
// =============================================================================

export function FixStepCard({
  title,
  description,
  difficulty,
  fixType,
  issuesCount,
  filePath,
  wcagCriteria,
  codeSnippet,
  steps,
  resources,
}: FixStepCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const difficultyConfig = getDifficultyConfig(difficulty);
  const fixTypeConfig = getFixTypeConfig(fixType);
  const FixTypeIcon = fixTypeConfig.icon;

  const hasDetails = codeSnippet || steps || resources || wcagCriteria;

  return (
    <div className={`border ${difficultyConfig.borderClass} rounded-xl overflow-hidden bg-white`}>
      {/* Header */}
      <div
        className={`px-4 py-3 flex items-center justify-between ${
          hasDetails ? 'cursor-pointer hover:bg-gray-50' : ''
        } transition`}
        onClick={() => hasDetails && setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 ${difficultyConfig.bgClass} rounded-lg`}>
            <FixTypeIcon className={`w-4 h-4 ${difficultyConfig.textClass}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-gray-900">{title}</h4>
              {issuesCount && issuesCount > 1 && (
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {issuesCount}x
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 line-clamp-1">{description}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Difficulty Badge */}
          <span className={`px-2 py-1 ${difficultyConfig.bgClass} ${difficultyConfig.textClass} text-xs font-medium rounded-lg`}>
            {difficultyConfig.label}
          </span>

          {/* Fix Type Badge */}
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-lg">
            {fixTypeConfig.label}
          </span>

          {/* Expand Button */}
          {hasDetails && (
            <button className="p-1 hover:bg-gray-100 rounded-lg transition">
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && hasDetails && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-100 space-y-4">
          {/* File Path */}
          {filePath && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <FileCode className="w-4 h-4" />
              <code className="bg-gray-100 px-2 py-0.5 rounded">{filePath}</code>
            </div>
          )}

          {/* WCAG Criteria */}
          {wcagCriteria && wcagCriteria.length > 0 && (
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5" />
              <div>
                <span className="text-sm font-medium text-gray-700">WCAG-Kriterien:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {wcagCriteria.map((criterion, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded"
                    >
                      {criterion}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Code Snippet */}
          {codeSnippet && (
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              <pre className="p-4 text-sm text-green-400 overflow-x-auto">
                <code>{codeSnippet}</code>
              </pre>
            </div>
          )}

          {/* Manual Steps */}
          {steps && steps.length > 0 && (
            <div className="space-y-2">
              <span className="text-sm font-medium text-gray-700">Schritte:</span>
              <ol className="space-y-2">
                {steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-600">
                    <span className="flex-shrink-0 w-5 h-5 bg-gray-200 text-gray-600 rounded-full flex items-center justify-center text-xs font-medium">
                      {i + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Resources */}
          {resources && resources.length > 0 && (
            <div className="space-y-2">
              <span className="text-sm font-medium text-gray-700">Hilfreiche Links:</span>
              <div className="flex flex-wrap gap-2">
                {resources.map((resource, i) => (
                  <a
                    key={i}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-lg transition"
                  >
                    {resource.title}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FixStepCard;

