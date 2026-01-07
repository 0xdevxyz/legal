'use client';

import React, { useState } from 'react';
import { Code, Eye, FileCode } from 'lucide-react';

interface FixPreviewProps {
  beforeCode: string;
  afterCode: string;
  language?: string;
  fileName?: string;
}

export const FixPreview: React.FC<FixPreviewProps> = ({
  beforeCode,
  afterCode,
  language = 'html',
  fileName = 'index.html'
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'unified'>('side-by-side');

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-white">
            <FileCode className="w-5 h-5" />
            <span className="font-semibold">{fileName}</span>
            <span className="text-xs bg-white/20 px-2 py-1 rounded">{language.toUpperCase()}</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-white text-blue-600 font-semibold'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                viewMode === 'unified'
                  ? 'bg-white text-blue-600 font-semibold'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              Unified
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'side-by-side' ? (
        <div className="grid grid-cols-2 divide-x divide-gray-200">
          {/* Before */}
          <div className="p-4 bg-red-50">
            <div className="flex items-center gap-2 mb-3 text-red-700 font-semibold">
              <Code className="w-4 h-4" />
              <span>Vorher</span>
            </div>
            <pre className="text-xs font-mono overflow-x-auto bg-white p-3 rounded border border-red-200">
              <code className="text-red-900">{beforeCode}</code>
            </pre>
          </div>

          {/* After */}
          <div className="p-4 bg-green-50">
            <div className="flex items-center gap-2 mb-3 text-green-700 font-semibold">
              <Eye className="w-4 h-4" />
              <span>Nachher (mit Fix)</span>
            </div>
            <pre className="text-xs font-mono overflow-x-auto bg-white p-3 rounded border border-green-200">
              <code className="text-green-900">{afterCode}</code>
            </pre>
          </div>
        </div>
      ) : (
        <div className="p-4">
          <pre className="text-xs font-mono overflow-x-auto bg-gray-900 text-gray-100 p-4 rounded">
            {generateUnifiedDiff(beforeCode, afterCode)}
          </pre>
        </div>
      )}

      {/* Legend */}
      <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
        <div className="flex gap-4 text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-200 rounded"></div>
            <span>Entfernt</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-200 rounded"></div>
            <span>Hinzugefügt</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Simple unified diff generator (basic version)
function generateUnifiedDiff(before: string, after: string): string {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');
  
  let diff = '';
  const maxLines = Math.max(beforeLines.length, afterLines.length);
  
  for (let i = 0; i < maxLines; i++) {
    const beforeLine = beforeLines[i] || '';
    const afterLine = afterLines[i] || '';
    
    if (beforeLine === afterLine) {
      diff += `  ${beforeLine}\n`;
    } else {
      if (beforeLine) {
        diff += `- ${beforeLine}\n`;
      }
      if (afterLine) {
        diff += `+ ${afterLine}\n`;
      }
    }
  }
  
  return diff;
}

