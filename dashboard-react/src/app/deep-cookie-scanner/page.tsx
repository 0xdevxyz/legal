'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, Loader2, CheckCircle2, AlertTriangle, Download, Plus } from 'lucide-react';
import Link from 'next/link';

interface Service {
  name: string;
  category: 'necessary' | 'functional' | 'analytics' | 'marketing';
  cookies: string[];
  total_cookies: number;
  total_requests: number;
  can_block: boolean;
  description: string;
}

interface ScanResult {
  scan_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  url: string;
  total_cookies?: number;
  unique_services?: number;
  total_requests?: number;
  services_detected?: string[];
  scan_duration_seconds?: number;
  progress_percent?: number;
  error?: string;
}

interface ExportData {
  scan_id: number;
  services: Service[];
  import_ready: boolean;
  message: string;
}

export default function DeepCookieScannerPage() {
  const [inputUrl, setInputUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentScan, setCurrentScan] = useState<ScanResult | null>(null);
  const [exportData, setExportData] = useState<ExportData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState({ scans_used: 0, scans_limit: 5 });
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  const handleStartScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!inputUrl.trim()) {
      setError('Please enter a website URL');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v2/deep-cookie-scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: inputUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start scan');
      }

      const data = await response.json();
      setCurrentScan({
        scan_id: data.scan_id,
        status: 'pending',
        url: data.message || inputUrl,
        progress_percent: 0,
      });
      setUsage(data.usage);
      setInputUrl('');

      pollScanStatus(data.scan_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsLoading(false);
    }
  };

  const pollScanStatus = useCallback((scanId: number) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v2/deep-cookie-scan/${scanId}`);
        if (!response.ok) throw new Error('Failed to fetch scan status');

        const data = await response.json();
        setCurrentScan(data);

        if (data.status === 'completed') {
          clearInterval(interval);
          setPollInterval(null);
          await fetchExportData(scanId);
          setIsLoading(false);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setPollInterval(null);
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 5000);

    setPollInterval(interval);
  }, []);

  const fetchExportData = async (scanId: number) => {
    try {
      const response = await fetch(`/api/v2/deep-cookie-scan/${scanId}/export`);
      if (!response.ok) throw new Error('Failed to fetch export data');
      const data = await response.json();
      setExportData(data);
    } catch (err) {
      console.error('Export fetch error:', err);
    }
  };

  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [pollInterval]);

  return (
    <div className="px-4 sm:px-6 py-6">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-bold dark:text-white text-gray-900 mb-2">Deep Cookie Scanner</h1>
          <p className="dark:text-zinc-400 text-gray-600">
            Scan your website for all cookies, tracking pixels, and analytics services
          </p>
        </div>

        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm dark:text-zinc-400 text-gray-600">Scans this month</p>
              <p className="text-2xl font-bold dark:text-white text-gray-900">
                {usage.scans_used} / {usage.scans_limit}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm dark:text-zinc-400 text-gray-600">Remaining</p>
              <p className="text-2xl font-bold text-blue-400">
                {Math.max(0, usage.scans_limit - usage.scans_used)}
              </p>
            </div>
          </div>
          <div className="mt-3 bg-zinc-700/50 rounded h-2">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded transition-all"
              style={{ width: `${(usage.scans_used / usage.scans_limit) * 100}%` }}
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-red-300">{error}</div>
          </div>
        )}

        <form onSubmit={handleStartScan} className="mb-8">
          <div className="flex gap-3">
            <input
              type="url"
              placeholder="https://example.com"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              disabled={isLoading}
              className="flex-1 px-4 py-3 bg-zinc-700/50 border border-zinc-600/50 rounded-lg dark:text-white text-gray-900 placeholder-zinc-500
                         focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20
                         disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={isLoading || usage.scans_used >= usage.scans_limit}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 dark:text-white text-gray-900 rounded-lg font-semibold
                         hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed
                         transition flex items-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Scan starten
            </button>
          </div>
          <p className="text-sm dark:text-zinc-500 text-gray-500 mt-2">
            Scan takes ~3 minutes. We detect all cookies and classify them by service.
          </p>
        </form>

        {currentScan && (
          <div className="space-y-6">
            <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm dark:text-zinc-400 text-gray-600">Scanning: {currentScan.url}</p>
                  <p className="text-lg font-semibold dark:text-white text-gray-900 mt-1">
                    {currentScan.status === 'pending' && 'Queued...'}
                    {currentScan.status === 'running' && 'Scanning in progress'}
                    {currentScan.status === 'completed' && 'Scan completed'}
                    {currentScan.status === 'failed' && 'Scan failed'}
                  </p>
                </div>
                <div>
                  {currentScan.status === 'running' && (
                    <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                  )}
                  {currentScan.status === 'completed' && (
                    <CheckCircle2 className="w-6 h-6 text-green-400" />
                  )}
                  {currentScan.status === 'failed' && (
                    <AlertTriangle className="w-6 h-6 text-red-400" />
                  )}
                </div>
              </div>

              {(currentScan.status === 'pending' || currentScan.status === 'running') && (
                <div className="mb-4">
                  <div className="bg-zinc-700/50 rounded h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded transition-all"
                      style={{ width: `${currentScan.progress_percent || 0}%` }}
                    />
                  </div>
                  <p className="text-xs dark:text-zinc-400 text-gray-600 mt-2">
                    {currentScan.progress_percent || 0}% complete
                  </p>
                </div>
              )}

              {currentScan.status === 'failed' && currentScan.error && (
                <div className="text-red-300 text-sm">{currentScan.error}</div>
              )}
            </div>

            {currentScan.status === 'completed' && currentScan.total_cookies !== undefined && (
              <>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
                    <p className="text-sm dark:text-zinc-400 text-gray-600">Total Cookies</p>
                    <p className="text-3xl font-bold dark:text-white text-gray-900 mt-2">{currentScan.total_cookies}</p>
                  </div>
                  <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
                    <p className="text-sm dark:text-zinc-400 text-gray-600">Services Detected</p>
                    <p className="text-3xl font-bold text-purple-400 mt-2">{currentScan.unique_services}</p>
                  </div>
                  <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
                    <p className="text-sm dark:text-zinc-400 text-gray-600">Tracking Requests</p>
                    <p className="text-3xl font-bold text-blue-400 mt-2">{currentScan.total_requests}</p>
                  </div>
                </div>

                {exportData && (
                  <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-6">
                    <h2 className="text-xl font-bold dark:text-white text-gray-900 mb-4">Detected Services</h2>
                    <div className="space-y-3">
                      {exportData.services.map((service, idx) => (
                        <div
                          key={idx}
                          className="flex items-start justify-between p-4 bg-zinc-700/50 rounded-lg border border-zinc-600/30 hover:border-zinc-600/50 transition"
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold dark:text-white text-gray-900">{service.name}</h3>
                              <span
                                className={`text-xs px-2 py-1 rounded ${
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
                            <p className="text-sm dark:text-zinc-400 text-gray-600 mt-1">{service.description}</p>
                            <div className="flex gap-4 mt-2 text-xs dark:text-zinc-500 text-gray-500">
                              <span>{service.total_cookies} cookies</span>
                              <span>{service.total_requests} requests</span>
                            </div>
                            {service.cookies.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {service.cookies.slice(0, 5).map((cookie, i) => (
                                  <span key={i} className="text-xs bg-zinc-600/50 dark:text-zinc-300 text-gray-700 px-2 py-1 rounded">
                                    {cookie}
                                  </span>
                                ))}
                                {service.cookies.length > 5 && (
                                  <span className="text-xs bg-zinc-600/50 dark:text-zinc-400 text-gray-600 px-2 py-1 rounded">
                                    +{service.cookies.length - 5} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                          <Link
                            href={`/dashboard/cookie-banner?import_scan=${currentScan.scan_id}&service=${encodeURIComponent(service.name)}`}
                            className="ml-4 px-4 py-2 bg-green-600/20 text-green-400 rounded font-semibold hover:bg-green-600/30
                                     transition flex items-center gap-2 flex-shrink-0"
                          >
                            <Plus className="w-4 h-4" />
                            Hinzufügen
                          </Link>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      const json = JSON.stringify(exportData, null, 2);
                      const blob = new Blob([json], { type: 'application/json' });
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `cookie-scan-${currentScan.scan_id}.json`;
                      a.click();
                      window.URL.revokeObjectURL(url);
                    }}
                    className="flex-1 px-4 py-3 bg-zinc-700/50 border border-zinc-600/50 dark:text-white text-gray-900 rounded-lg
                             font-semibold hover:bg-zinc-600/50 transition flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Export JSON
                  </button>
                  <button
                    onClick={() => {
                      setCurrentScan(null);
                      setExportData(null);
                    }}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 dark:text-white text-gray-900 rounded-lg
                             font-semibold hover:from-blue-700 hover:to-purple-700 transition"
                  >
                    Neuen Scan starten
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
