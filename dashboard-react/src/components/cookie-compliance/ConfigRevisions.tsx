/**
 * Config Revisions & Import/Export
 * Versionshistorie und Backup-Funktionen
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  History, Download, Upload, Eye, Clock, RefreshCw, 
  ChevronDown, ChevronUp, CheckCircle, AlertCircle 
} from 'lucide-react';

interface ConfigRevisionsProps {
  siteId: string;
  config: any;
  onImport: (config: any) => Promise<boolean>;
}

interface Revision {
  revision: number;
  snapshot: any;
  changes: string;
  created_at: string;
}

export default function ConfigRevisions({ siteId, config, onImport }: ConfigRevisionsProps) {
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedRevision, setExpandedRevision] = useState<number | null>(null);
  const [importing, setImporting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  useEffect(() => {
    loadRevisions();
  }, [siteId]);

  const loadRevisions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/revisions/${siteId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setRevisions(data.revisions || []);
        }
      }
    } catch (error) {
      console.error('Error loading revisions:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/export/${siteId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const blob = new Blob([JSON.stringify(data.export, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `complyo-config-${siteId}-${new Date().toISOString().split('T')[0]}.json`;
          a.click();
          URL.revokeObjectURL(url);
          
          setMessage({ type: 'success', text: 'Konfiguration exportiert!' });
          setTimeout(() => setMessage(null), 3000);
        }
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Export fehlgeschlagen' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const importConfig = async (file: File) => {
    setImporting(true);
    try {
      const text = await file.text();
      const importData = JSON.parse(text);
      
      const response = await fetch(`${API_URL}/api/cookie-compliance/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: siteId,
          import: importData
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMessage({ type: 'success', text: 'Konfiguration importiert!' });
          // Reload the page to apply changes
          setTimeout(() => window.location.reload(), 1500);
        } else {
          setMessage({ type: 'error', text: data.error || 'Import fehlgeschlagen' });
        }
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Ungültige Import-Datei' });
    } finally {
      setImporting(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const restoreRevision = async (revision: Revision) => {
    if (!confirm(`Möchten Sie wirklich zur Revision ${revision.revision} zurückkehren?`)) {
      return;
    }
    
    try {
      const success = await onImport(revision.snapshot);
      if (success) {
        setMessage({ type: 'success', text: `Revision ${revision.revision} wiederhergestellt` });
        loadRevisions();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Wiederherstellung fehlgeschlagen' });
    }
    setTimeout(() => setMessage(null), 3000);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unbekannt';
    return new Date(dateString).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Message Alert */}
      {message && (
        <Card className={`${message.type === 'success' ? 'bg-green-500/20 border-green-500' : 'bg-red-500/20 border-red-500'}`}>
          <CardContent className="py-3">
            <div className="flex items-center gap-2">
              {message.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-400" />
              )}
              <span className="text-white">{message.text}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Import/Export Section */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-400" />
            Import / Export
          </CardTitle>
          <CardDescription>
            Sichern Sie Ihre Konfiguration oder übertragen Sie sie auf andere Websites
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button
              onClick={exportConfig}
              className="flex-1 bg-blue-500 hover:bg-blue-600 gap-2"
            >
              <Download className="w-4 h-4" />
              Konfiguration exportieren
            </Button>
            
            <label className="flex-1">
              <input
                type="file"
                accept=".json"
                onChange={(e) => e.target.files?.[0] && importConfig(e.target.files[0])}
                className="hidden"
              />
              <Button
                as="span"
                variant="outline"
                className="w-full gap-2 cursor-pointer"
                disabled={importing}
              >
                <Upload className="w-4 h-4" />
                {importing ? 'Importiere...' : 'Konfiguration importieren'}
              </Button>
            </label>
          </div>
          
          <p className="text-xs text-gray-500">
            Die Export-Datei enthält alle Einstellungen außer sensiblen Daten wie User-IDs.
          </p>
        </CardContent>
      </Card>

      {/* Revision History */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <History className="w-5 h-5 text-purple-400" />
                Revisionen
              </CardTitle>
              <CardDescription>
                Änderungshistorie Ihrer Cookie-Banner Konfiguration
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadRevisions}
              disabled={loading}
              className="gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Aktualisieren
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {revisions.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Keine Revisionen gefunden.</p>
              <p className="text-sm">Änderungen werden automatisch gespeichert.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {revisions.map((revision) => (
                <div 
                  key={revision.revision}
                  className="border border-gray-700 rounded-lg overflow-hidden"
                >
                  <div 
                    className="flex items-center justify-between p-4 bg-gray-900/50 cursor-pointer hover:bg-gray-900/70 transition-colors"
                    onClick={() => setExpandedRevision(
                      expandedRevision === revision.revision ? null : revision.revision
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Badge className="bg-purple-500/20 text-purple-400">
                        v{revision.revision}
                      </Badge>
                      <div>
                        <div className="text-sm text-white">
                          {revision.changes || 'Konfigurationsänderung'}
                        </div>
                        <div className="text-xs text-gray-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(revision.created_at)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          restoreRevision(revision);
                        }}
                        className="text-xs"
                      >
                        Wiederherstellen
                      </Button>
                      {expandedRevision === revision.revision ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                  
                  {expandedRevision === revision.revision && (
                    <div className="p-4 bg-gray-900/30 border-t border-gray-700">
                      <h4 className="text-sm font-medium text-gray-300 mb-2">
                        Konfiguration (Revision {revision.revision})
                      </h4>
                      <pre className="text-xs bg-gray-900 p-3 rounded overflow-auto max-h-48 text-green-400">
                        {JSON.stringify(revision.snapshot, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Current Config Hash */}
      <Card className="bg-gray-900/50 border-gray-700">
        <CardContent className="py-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Aktuelle Konfigurations-ID:</span>
            <code className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
              {config?.config_hash || 'Nicht berechnet'}
            </code>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
