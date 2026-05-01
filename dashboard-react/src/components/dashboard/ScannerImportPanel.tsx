import React, { useState, useEffect } from 'react';
import { Zap, Plus, Loader2, AlertCircle } from 'lucide-react';

interface ScannedService {
  name: string;
  category: 'necessary' | 'functional' | 'analytics' | 'marketing';
  cookies: string[];
  total_cookies: number;
  total_requests: number;
  can_block: boolean;
  description: string;
}

interface ScannerImportPanelProps {
  websiteId?: string;
  onServicesImported: (services: ScannedService[]) => void;
}

export function ScannerImportPanel({ websiteId, onServicesImported }: ScannerImportPanelProps) {
  const [showPanel, setShowPanel] = useState(false);
  const [scans, setScans] = useState<Array<{ scan_id: number; url: string; created_at: string }>>([]);
  const [selectedScan, setSelectedScan] = useState<number | null>(null);
  const [scanData, setScanData] = useState<{
    services: ScannedService[];
    selected: Set<string>;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available scans on mount
  useEffect(() => {
    if (showPanel) {
      fetchScans();
    }
  }, [showPanel]);

  // Fetch user's recent scans
  const fetchScans = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v2/deep-cookie-scan/my-scans?limit=10');
      if (!response.ok) throw new Error('Failed to fetch scans');
      const data = await response.json();
      setScans(data.scans);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scans');
    } finally {
      setIsLoading(false);
    }
  };

  // Load scan details and export data
  const loadScanData = async (scanId: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v2/deep-cookie-scan/${scanId}/export`);
      if (!response.ok) throw new Error('Failed to fetch scan data');
      const data = await response.json();
      
      setScanData({
        services: data.services,
        selected: new Set<string>(),
      });
      setSelectedScan(scanId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan data');
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle service selection
  const toggleService = (serviceName: string) => {
    if (!scanData) return;
    
    const newSelected = new Set(scanData.selected);
    if (newSelected.has(serviceName)) {
      newSelected.delete(serviceName);
    } else {
      newSelected.add(serviceName);
    }
    
    setScanData({
      ...scanData,
      selected: newSelected,
    });
  };

  // Import selected services
  const importServices = () => {
    if (!scanData) return;
    
    const selectedServices = scanData.services.filter(s => scanData.selected.has(s.name));
    onServicesImported(selectedServices);
    setShowPanel(false);
  };

  if (!showPanel) {
    return (
      <button
        onClick={() => setShowPanel(true)}
        className="w-full px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg
                 font-semibold hover:from-green-700 hover:to-emerald-700 transition flex items-center justify-center gap-2"
      >
        <Zap className="w-4 h-4" />
        Von Deep Cookie Scanner importieren
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-700/50 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-zinc-800/95 border-b border-zinc-700/50 px-6 py-4 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Scanner-Ergebnisse importieren</h2>
            <p className="text-sm text-zinc-400 mt-1">
              Wähle einen Scan und importiere die erkannten Services
            </p>
          </div>
          <button
            onClick={() => setShowPanel(false)}
            className="text-zinc-400 hover:text-white text-2xl font-light leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="text-red-300 text-sm">{error}</div>
            </div>
          )}

          {/* Scan Selection */}
          {!selectedScan ? (
            <div className="space-y-4">
              <p className="text-sm text-zinc-400">Verfügbare Scans:</p>
              
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                </div>
              ) : scans.length === 0 ? (
                <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-8 text-center">
                  <p className="text-zinc-400">Keine Scans gefunden</p>
                  <a
                    href="/deep-cookie-scanner"
                    className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block"
                  >
                    Starte deinen ersten Scan →
                  </a>
                </div>
              ) : (
                <div className="space-y-2">
                  {scans.map((scan) => (
                    <button
                      key={scan.scan_id}
                      onClick={() => loadScanData(scan.scan_id)}
                      className="w-full p-4 bg-zinc-800/50 border border-zinc-700/50 rounded-lg hover:border-blue-500/50
                               text-left transition flex items-center justify-between group"
                    >
                      <div>
                        <p className="text-white font-semibold">{scan.url}</p>
                        <p className="text-sm text-zinc-400 mt-1">
                          {new Date(scan.created_at).toLocaleDateString('de-DE')}
                        </p>
                      </div>
                      <Plus className="w-5 h-5 text-zinc-400 group-hover:text-blue-400 transition" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Scan Details & Service Selection */
            <>
              <button
                onClick={() => {
                  setSelectedScan(null);
                  setScanData(null);
                }}
                className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1"
              >
                ← Zurück zur Scan-Liste
              </button>

              {scanData && (
                <>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-3">
                      <p className="text-xs text-zinc-400">Gesamt Services</p>
                      <p className="text-2xl font-bold text-white mt-1">{scanData.services.length}</p>
                    </div>
                    <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-3">
                      <p className="text-xs text-zinc-400">Ausgewählt</p>
                      <p className="text-2xl font-bold text-blue-400 mt-1">{scanData.selected.size}</p>
                    </div>
                    <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-3">
                      <p className="text-xs text-zinc-400">Blockierbar</p>
                      <p className="text-2xl font-bold text-green-400 mt-1">
                        {scanData.services.filter(s => s.can_block).length}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-white">Services wählen:</p>
                      <button
                        onClick={() => {
                          const newSelected = new Set(
                            scanData.services.map(s => s.name)
                          );
                          setScanData({ ...scanData, selected: newSelected });
                        }}
                        className="text-xs text-blue-400 hover:text-blue-300"
                      >
                        Alle wählen
                      </button>
                    </div>
                    
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {scanData.services.map((service) => (
                        <label
                          key={service.name}
                          className="flex items-start gap-3 p-3 bg-zinc-800/50 border border-zinc-700/50 rounded-lg
                                   hover:border-zinc-600/50 cursor-pointer transition"
                        >
                          <input
                            type="checkbox"
                            checked={scanData.selected.has(service.name)}
                            onChange={() => toggleService(service.name)}
                            className="mt-1 w-4 h-4 accent-blue-500"
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-white">{service.name}</span>
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${
                                  service.category === 'necessary'
                                    ? 'bg-blue-500/20 text-blue-300'
                                    : service.category === 'functional'
                                    ? 'bg-cyan-500/20 text-cyan-300'
                                    : service.category === 'analytics'
                                    ? 'bg-purple-500/20 text-purple-300'
                                    : 'bg-amber-500/20 text-amber-300'
                                }`}
                              >
                                {service.category}
                              </span>
                            </div>
                            <p className="text-xs text-zinc-400 mt-1">{service.description}</p>
                            <p className="text-xs text-zinc-500 mt-1">
                              {service.total_cookies} cookies · {service.total_requests} requests
                            </p>
                          </div>
                          {!service.can_block && (
                            <span className="text-xs text-zinc-500 px-2 py-1 bg-zinc-700/50 rounded">
                              Notwendig
                            </span>
                          )}
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {selectedScan && scanData && (
          <div className="sticky bottom-0 bg-zinc-800/95 border-t border-zinc-700/50 px-6 py-4 flex gap-3">
            <button
              onClick={() => {
                setSelectedScan(null);
                setScanData(null);
              }}
              className="px-4 py-2 bg-zinc-700/50 text-white rounded-lg font-semibold hover:bg-zinc-700 transition"
            >
              Abbrechen
            </button>
            <button
              onClick={importServices}
              disabled={scanData.selected.size === 0}
              className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg
                       font-semibold hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              {scanData.selected.size} Service(s) importieren
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Usage in CookieBannerDesigner.tsx:
// Replace the "Coming Soon" section (~line 333) with:
//
// <ScannerImportPanel
//   websiteId={websiteId}
//   onServicesImported={(services) => {
//     services.forEach(service => {
//       // Convert scanned service to banner service format
//       addServiceToConsent({
//         name: service.name,
//         category: service.category,
//         necessary: service.category === 'necessary',
//         cookies: service.cookies,
//         description: service.description,
//       });
//     });
//   }}
// />
