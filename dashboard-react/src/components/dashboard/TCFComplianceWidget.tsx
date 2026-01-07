'use client';

import React, { useState, useEffect } from 'react';
import { Shield, CheckCircle, AlertTriangle, Info, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

interface TCFData {
  has_tcf: boolean;
  tcf_version?: string;
  cmp_name?: string;
  cmp_id?: number;
  tc_string_found: boolean;
  vendor_count: number;
  detected_vendors?: Vendor[];
  issues?: TCFIssue[];
}

interface Vendor {
  vendor_id: string;
  vendor_name: string;
  detected_from: string;
  requires_consent: boolean;
  purposes?: Purpose[];
}

interface Purpose {
  id: number;
  name: string;
  legal_basis: string;
}

interface TCFIssue {
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
}

interface TCFComplianceWidgetProps {
  scanId?: string;
  tcfData?: TCFData;
}

export default function TCFComplianceWidget({ scanId, tcfData }: TCFComplianceWidgetProps) {
  const [expanded, setExpanded] = useState(false);
  const [vendorsExpanded, setVendorsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fullTCFData, setFullTCFData] = useState<TCFData | null>(tcfData || null);

  useEffect(() => {
    if (tcfData) {
      setFullTCFData(tcfData);
    }
  }, [tcfData]);

  // Lade vollständige TCF Daten wenn scanId vorhanden
  useEffect(() => {
    if (scanId && !tcfData) {
      loadTCFData();
    }
  }, [scanId]);

  const loadTCFData = async () => {
    if (!scanId) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/tcf/status/${scanId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFullTCFData(data);
      }
    } catch (error) {
      console.error('Failed to load TCF data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!fullTCFData) {
    return null;
  }

  const { has_tcf, tcf_version, cmp_name, tc_string_found, vendor_count, detected_vendors, issues } = fullTCFData;

  // Bestimme Status
  let statusColor = 'gray';
  let statusText = 'Nicht verfügbar';
  let statusIcon = <Info className="w-5 h-5" />;

  if (has_tcf) {
    if (tc_string_found && (!issues || issues.length === 0)) {
      statusColor = 'green';
      statusText = 'TCF 2.2 Konform';
      statusIcon = <CheckCircle className="w-5 h-5" />;
    } else if (tc_string_found) {
      statusColor = 'yellow';
      statusText = 'TCF mit Problemen';
      statusIcon = <AlertTriangle className="w-5 h-5" />;
    } else {
      statusColor = 'orange';
      statusText = 'TCF unvollständig';
      statusIcon = <AlertTriangle className="w-5 h-5" />;
    }
  }

  const bgColor = {
    'green': 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    'yellow': 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    'orange': 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
    'gray': 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
  }[statusColor];

  const textColor = {
    'green': 'text-green-700 dark:text-green-300',
    'yellow': 'text-yellow-700 dark:text-yellow-300',
    'orange': 'text-orange-700 dark:text-orange-300',
    'gray': 'text-gray-700 dark:text-gray-300'
  }[statusColor];

  return (
    <div className={`border rounded-lg p-4 ${bgColor}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`${textColor}`}>
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              IAB TCF 2.2 Status
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Transparency & Consent Framework
            </p>
          </div>
        </div>
        
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${textColor} bg-white/50 dark:bg-black/20`}>
          {statusIcon}
          <span className="text-sm font-medium">{statusText}</span>
        </div>
      </div>

      {/* Main Info */}
      <div className="space-y-2 mb-3">
        {has_tcf ? (
          <>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">CMP Anbieter:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {cmp_name || 'Unbekannt'}
              </span>
            </div>
            
            {tcf_version && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">TCF Version:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  v{tcf_version}
                </span>
              </div>
            )}
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">TC String:</span>
              <span className={`font-medium ${tc_string_found ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {tc_string_found ? '✓ Vorhanden' : '✗ Nicht gefunden'}
              </span>
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Erkannte Vendors:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {vendor_count}
              </span>
            </div>
          </>
        ) : (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <p>TCF 2.2 ist nicht auf dieser Website implementiert.</p>
            <p className="mt-1 text-xs">
              <strong>Hinweis:</strong> TCF ist optional und primär für Publisher mit programmatic advertising relevant.
            </p>
          </div>
        )}
      </div>

      {/* Issues */}
      {issues && issues.length > 0 && (
        <div className="mb-3 p-3 bg-white/50 dark:bg-black/20 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
            Gefundene Probleme ({issues.length})
          </h4>
          <div className="space-y-2">
            {issues.slice(0, expanded ? undefined : 2).map((issue, idx) => (
              <div key={idx} className="text-sm">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{issue.title}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{issue.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {issues.length > 2 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              {expanded ? 'Weniger anzeigen' : `${issues.length - 2} weitere anzeigen`}
              {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}
        </div>
      )}

      {/* Vendors List */}
      {has_tcf && detected_vendors && detected_vendors.length > 0 && (
        <div className="mb-3">
          <button
            onClick={() => setVendorsExpanded(!vendorsExpanded)}
            className="w-full flex items-center justify-between p-2 bg-white/50 dark:bg-black/20 rounded-lg hover:bg-white/70 dark:hover:bg-black/30 transition-colors"
          >
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              Vendors ({vendor_count})
            </span>
            {vendorsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          
          {vendorsExpanded && (
            <div className="mt-2 space-y-2 max-h-64 overflow-y-auto">
              {detected_vendors.map((vendor, idx) => (
                <div key={idx} className="p-2 bg-white/50 dark:bg-black/20 rounded text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900 dark:text-white">{vendor.vendor_name}</span>
                    <span className="text-xs text-gray-500">ID: {vendor.vendor_id}</span>
                  </div>
                  {vendor.purposes && vendor.purposes.length > 0 && (
                    <div className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                      <strong>Purposes:</strong> {vendor.purposes.map(p => p.name).join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Learn More */}
      <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
        <a
          href="https://iabeurope.eu/tcf-2-0/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
        >
          Mehr über TCF 2.2 erfahren
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}

