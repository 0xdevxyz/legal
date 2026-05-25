'use client';

import React, { useState } from 'react';
import {
  RefreshCw, CheckCircle, AlertTriangle, Clock,
  Plus, Minus, Shield, Loader2, Eye, Info,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api-client';

interface ScanMonitorProps {
  siteId: string;
  websiteUrl?: string;
  lastScanDate?: string;
  storedServices?: string[];
}

const ScanMonitor: React.FC<ScanMonitorProps> = ({
  siteId,
  websiteUrl,
  lastScanDate,
  storedServices = [],
}) => {
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  const runCheck = async () => {
    if (!websiteUrl || !siteId) return;
    setChecking(true);
    try {
      const data = await apiClient.post(`/api/cookie-compliance/monitor/check/${siteId}`, {
        url: websiteUrl,
      }) as any;
      setResult(data);
      setLastChecked(new Date().toISOString());
    } catch {
      setResult({ success: false, error: 'Überprüfung fehlgeschlagen. Bitte erneut versuchen.' });
    } finally {
      setChecking(false);
    }
  };

  const hasChanges = result?.has_changes;
  const newServices: any[] = result?.new_services || [];
  const removedServices: string[] = result?.removed_services || [];

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('de-DE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

  return (
    <div className="space-y-5">
      {/* Status Card */}
      <Card className={`border-2 transition-all ${
        !result
          ? 'border-gray-700 bg-gray-800/30'
          : !result.success
            ? 'border-red-500/40 bg-red-500/5'
            : hasChanges
              ? 'border-yellow-500/50 bg-yellow-500/5'
              : 'border-green-500/40 bg-green-500/5'
      }`}>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              <div className={`p-3 rounded-full flex-shrink-0 ${
                !result
                  ? 'bg-gray-700/50'
                  : !result.success
                    ? 'bg-red-500/20'
                    : hasChanges
                      ? 'bg-yellow-500/20'
                      : 'bg-green-500/20'
              }`}>
                {!result
                  ? <Shield className="w-6 h-6 text-gray-400" />
                  : !result.success
                    ? <AlertTriangle className="w-6 h-6 text-red-400" />
                    : hasChanges
                      ? <AlertTriangle className="w-6 h-6 text-yellow-400" />
                      : <CheckCircle className="w-6 h-6 text-green-400" />
                }
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-white text-lg">
                  {!result
                    ? 'Überwachung bereit'
                    : !result.success
                      ? 'Überprüfung fehlgeschlagen'
                      : hasChanges
                        ? 'Änderungen erkannt!'
                        : 'Keine Änderungen'}
                </h3>
                <p className="text-sm text-gray-400 mt-1">
                  {!result
                    ? 'Klicken Sie auf „Jetzt prüfen", um Ihre Website mit der gespeicherten Baseline zu vergleichen.'
                    : !result.success
                      ? result.error
                      : hasChanges
                        ? `${newServices.length} neue${newServices.length !== 1 ? '' : ''} und ${removedServices.length} entfernte Services seit dem letzten Scan.`
                        : 'Ihr Cookie-Banner ist aktuell. Die Website stimmt mit der gespeicherten Baseline überein.'}
                </p>

                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3">
                  {lastScanDate && (
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-gray-500" />
                      <span className="text-xs text-gray-500">Letzter Scan: {formatDate(lastScanDate)}</span>
                    </div>
                  )}
                  {lastChecked && (
                    <div className="flex items-center gap-1.5">
                      <RefreshCw className="w-3 h-3 text-gray-500" />
                      <span className="text-xs text-gray-500">Letzte Prüfung: {formatDate(lastChecked)}</span>
                    </div>
                  )}
                  {websiteUrl && (
                    <div className="flex items-center gap-1.5">
                      <Eye className="w-3 h-3 text-gray-500" />
                      <span className="text-xs text-gray-500 truncate max-w-xs">{websiteUrl}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <Button
              onClick={runCheck}
              disabled={checking || !websiteUrl}
              className={
                hasChanges
                  ? 'bg-yellow-500 hover:bg-yellow-600 text-black font-semibold flex-shrink-0'
                  : 'bg-orange-500 hover:bg-orange-600 text-white flex-shrink-0'
              }
            >
              {checking
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Prüft…</>
                : <><RefreshCw className="w-4 h-4 mr-2" />Jetzt prüfen</>
              }
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Changes Detail */}
      {result?.success && hasChanges && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {newServices.length > 0 && (
            <Card className="border-yellow-500/30 bg-yellow-500/5">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2 text-yellow-400">
                  <Plus className="w-4 h-4" />
                  Neu erkannt ({newServices.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {newServices.map((s: any) => (
                  <div
                    key={s.service_key}
                    className="flex items-center gap-2 p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/20"
                  >
                    <AlertTriangle className="w-3 h-3 text-yellow-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{s.name}</p>
                      <p className="text-xs text-gray-400 capitalize">{s.category}</p>
                    </div>
                  </div>
                ))}
                <p className="text-xs text-yellow-300/80 pt-1">
                  Diese Services sind auf Ihrer Website neu und noch nicht im Banner konfiguriert.
                </p>
              </CardContent>
            </Card>
          )}

          {removedServices.length > 0 && (
            <Card className="border-gray-600/40 bg-gray-800/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2 text-gray-400">
                  <Minus className="w-4 h-4" />
                  Nicht mehr gefunden ({removedServices.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {removedServices.map((key: string) => (
                  <div
                    key={key}
                    className="flex items-center gap-2 p-2 bg-gray-700/30 rounded-lg border border-gray-600/30"
                  >
                    <Minus className="w-3 h-3 text-gray-500 flex-shrink-0" />
                    <p className="text-xs text-gray-400">{key}</p>
                  </div>
                ))}
                <p className="text-xs text-gray-500 pt-1">
                  Diese Services wurden beim aktuellen Scan nicht mehr gefunden.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Current Baseline */}
      <Card className="border-gray-700 bg-gray-800/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-gray-300">
            <Eye className="w-4 h-4" />
            Gespeicherte Baseline
            <Badge variant="secondary" className="bg-gray-700 text-gray-400 border-gray-600 ml-1">
              {storedServices.length} Services
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {storedServices.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {storedServices.map((key) => (
                <Badge
                  key={key}
                  variant="secondary"
                  className="bg-gray-700/70 text-gray-300 border-gray-600 text-xs"
                >
                  {key}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Noch keine Services gespeichert. Führen Sie zuerst einen Scan durch (Tab „Services").
            </p>
          )}
        </CardContent>
      </Card>

      {/* Info Box */}
      <div className="flex items-start gap-3 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-blue-300 space-y-1">
          <p className="font-semibold text-blue-200">Wie funktioniert die Überwachung?</p>
          <p>
            Complyo scannt Ihre Website on-demand und vergleicht die gefundenen Services mit Ihrer gespeicherten Baseline.
            Bei Änderungen (neue Services oder entfernte Services) werden diese hier angezeigt, damit Sie Ihren
            Cookie-Banner jederzeit aktuell halten können.
          </p>
          <p className="text-blue-300/70">
            Empfehlung: Prüfen Sie Ihre Website nach jedem größeren Update oder Designänderung.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ScanMonitor;
