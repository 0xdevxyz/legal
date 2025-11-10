'use client';

import React, { useState } from 'react';
import { Check, Copy, Download, Image as ImageIcon, AlertCircle } from 'lucide-react';

/**
 * Bild-Issue Interface (matcht Backend BarrierefreiheitIssue)
 */
export interface ImageIssue {
  id: string;
  title: string;
  description: string;
  image_src: string;
  alt?: string;
  suggested_alt: string;
  screenshot_url?: string;  // Data URL oder https://
  fix_code?: string;
  auto_fixable: boolean;
  severity: 'error' | 'warning' | 'info';
  metadata?: {
    width?: number;
    height?: number;
    context?: string;
    is_visible?: boolean;
    has_title?: boolean;
    has_aria_label?: boolean;
  };
}

interface ImageIssuesListProps {
  issues: ImageIssue[];
  onApplyFix?: (issueId: string, fixCode: string) => void;
  siteUrl?: string;
}

/**
 * Dashboard-Komponente zur Anzeige von Barrierefreiheits-Problemen bei Bildern
 * Zeigt Screenshots, AI-Vorschläge und ermöglicht Auto-Fixes
 */
export function ImageIssuesList({ issues, onApplyFix, siteUrl }: ImageIssuesListProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!issues || issues.length === 0) {
    return (
      <div className="text-center py-12 px-4 bg-green-50 border border-green-200 rounded-lg">
        <Check className="w-12 h-12 text-green-600 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-green-900 mb-2">
          Alle Bilder haben Alt-Texte! 🎉
        </h3>
        <p className="text-green-700">
          Ihre Webseite erfüllt die WCAG-Kriterien für Bild-Beschreibungen.
        </p>
      </div>
    );
  }

  const handleCopyCode = async (issueId: string, code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedId(issueId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleApplyFix = (issueId: string, fixCode: string) => {
    if (onApplyFix) {
      onApplyFix(issueId, fixCode);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getSeverityIcon = (severity: string) => {
    const color = severity === 'error' || severity === 'critical' ? 'text-red-600' : 
                  severity === 'warning' ? 'text-yellow-600' : 'text-blue-600';
    return <AlertCircle className={`w-5 h-5 ${color}`} />;
  };

  return (
    <div className="space-y-4">
      {/* Zusammenfassung */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <ImageIcon className="w-6 h-6 text-gray-600" />
          <div>
            <h3 className="font-semibold text-gray-900">
              {issues.length} Bild{issues.length !== 1 ? 'er' : ''} ohne Alt-Text gefunden
            </h3>
            <p className="text-sm text-gray-600">
              Barrierefreiheit-Probleme, die behoben werden müssen
            </p>
          </div>
        </div>
      </div>

      {/* Issues-Liste */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {issues.map((issue) => (
          <div
            key={issue.id}
            className={`border rounded-lg overflow-hidden ${getSeverityColor(issue.severity)}`}
          >
            {/* Screenshot des Bildes */}
            {issue.screenshot_url ? (
              <div className="relative bg-gray-100 h-48 flex items-center justify-center overflow-hidden">
                <img
                  src={issue.screenshot_url}
                  alt="Screenshot des problematischen Bildes"
                  className="max-w-full max-h-full object-contain"
                  loading="lazy"
                />
                <div className="absolute top-2 right-2 flex gap-1">
                  {getSeverityIcon(issue.severity)}
                </div>
              </div>
            ) : (
              <div className="bg-gray-200 h-48 flex items-center justify-center">
                <ImageIcon className="w-12 h-12 text-gray-400" />
                <span className="ml-2 text-sm text-gray-500">Kein Screenshot verfügbar</span>
              </div>
            )}

            {/* Issue-Details */}
            <div className="p-4 space-y-3 bg-white">
              {/* Bild-URL */}
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">
                  Bild-Quelle
                </label>
                <div className="text-sm text-gray-700 truncate" title={issue.image_src}>
                  {issue.image_src.replace(siteUrl || '', '').substring(0, 40)}...
                </div>
              </div>

              {/* Problem-Beschreibung */}
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">
                  Problem
                </label>
                <div className="text-sm text-gray-900">
                  {issue.alt ? `Alt-Text vorhanden aber nicht ausreichend` : 'Kein Alt-Text'}
                </div>
              </div>

              {/* AI-Vorschlag */}
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <div className="flex items-start gap-2">
                  <span className="text-xs font-semibold text-green-700 uppercase">
                    AI-Vorschlag:
                  </span>
                </div>
                <div className="text-sm text-green-900 mt-1 font-medium">
                  "{issue.suggested_alt}"
                </div>
              </div>

              {/* Metadaten (optional expandierbar) */}
              {issue.metadata && (
                <button
                  onClick={() => setExpandedId(expandedId === issue.id ? null : issue.id)}
                  className="text-xs text-gray-500 hover:text-gray-700 underline"
                >
                  {expandedId === issue.id ? 'Weniger anzeigen' : 'Details anzeigen'}
                </button>
              )}

              {expandedId === issue.id && issue.metadata && (
                <div className="text-xs text-gray-600 space-y-1 pt-2 border-t">
                  <div>Größe: {issue.metadata.width}x{issue.metadata.height}px</div>
                  <div>Sichtbar: {issue.metadata.is_visible ? 'Ja' : 'Nein'}</div>
                  {issue.metadata.context && (
                    <div>Kontext: {issue.metadata.context.substring(0, 50)}...</div>
                  )}
                </div>
              )}

              {/* Aktionen */}
              <div className="flex gap-2 pt-2">
                {/* Fix-Code kopieren */}
                {issue.fix_code && (
                  <button
                    onClick={() => handleCopyCode(issue.id, issue.fix_code!)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded transition"
                    title="Code kopieren"
                  >
                    {copiedId === issue.id ? (
                      <>
                        <Check className="w-4 h-4 text-green-600" />
                        <span>Kopiert!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        <span>Code</span>
                      </>
                    )}
                  </button>
                )}

                {/* Auto-Fix anwenden */}
                {issue.auto_fixable && issue.fix_code && (
                  <button
                    onClick={() => handleApplyFix(issue.id, issue.fix_code!)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition"
                    title="Auto-Fix anwenden"
                  >
                    <Check className="w-4 h-4" />
                    <span>Fix</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sammel-Aktionen */}
      {issues.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Sammel-Aktionen</h4>
          <div className="flex gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded transition">
              <Download className="w-4 h-4" />
              Alle Fixes herunterladen
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition">
              <Check className="w-4 h-4" />
              Alle Auto-Fixes anwenden
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            💡 Tipp: Nutzen Sie das Complyo Smart-Widget für automatische Fixes auf Ihrer Live-Seite.
          </p>
        </div>
      )}
    </div>
  );
}

export default ImageIssuesList;

