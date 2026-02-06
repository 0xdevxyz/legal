'use client';

import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Download, RotateCcw, Clock, Server, GitBranch, Package } from 'lucide-react';

interface AuditEntry {
  id: string;
  fix_id: string;
  fix_category: string;
  action_type: string;
  deployment_method: string;
  applied_at: string;
  success: boolean;
  backup_id: string | null;
  rollback_available: boolean;
  error_message: string | null;
}

export const FixAuditLog: React.FC = () => {
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);

  useEffect(() => {
    fetchAuditLog();
  }, []);

  const fetchAuditLog = async () => {
    try {
      const response = await fetch('/api/v2/audit/log', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAuditLog(data.audit_log || []);
      }
    } catch (error) {
      console.error('Failed to fetch audit log:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (entry: AuditEntry) => {
    if (!entry.backup_id) {
      alert('Kein Backup vorhanden für diesen Eintrag.');
      return;
    }

    if (!confirm(`Möchten Sie wirklich zum Stand vor der Änderung zurückkehren?\n\nBackup: ${entry.backup_id}`)) {
      return;
    }

    // TODO: Rollback-Credentials-Modal öffnen
    alert('Rollback-Funktion: Credentials-Modal würde hier öffnen');
  };

  const getMethodIcon = (method: string) => {
    switch (method) {
      case 'ftp':
      case 'sftp':
        return Server;
      case 'github_pr':
        return GitBranch;
      case 'zip_download':
        return Download;
      default:
        return Package;
    }
  };

  const getMethodLabel = (method: string) => {
    switch (method) {
      case 'ftp':
        return 'FTP';
      case 'sftp':
        return 'SFTP';
      case 'github_pr':
        return 'GitHub PR';
      case 'zip_download':
        return 'ZIP Download';
      default:
        return method;
    }
  };

  const getActionLabel = (action: string) => {
    switch (action) {
      case 'generated':
        return 'Generiert';
      case 'downloaded':
        return 'Heruntergeladen';
      case 'applied':
        return 'Angewendet';
      case 'rolled_back':
        return 'Zurückgesetzt';
      case 'previewed':
        return 'Vorschau';
      default:
        return action;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Clock className="w-6 h-6 text-blue-600" />
          Audit Log
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Alle Ihre Fix-Aktionen werden hier rechtssicher dokumentiert.
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Aktion
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fix-Kategorie
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Methode
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Zeitpunkt
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Aktionen
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {auditLog.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  Noch keine Aktionen durchgeführt.
                </td>
              </tr>
            ) : (
              auditLog.map((entry) => {
                const MethodIcon = getMethodIcon(entry.deployment_method);
                
                return (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {entry.success ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        entry.action_type === 'applied'
                          ? 'bg-blue-100 text-blue-800'
                          : entry.action_type === 'downloaded'
                          ? 'bg-green-100 text-green-800'
                          : entry.action_type === 'rolled_back'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {getActionLabel(entry.action_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {entry.fix_category || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2 text-sm text-gray-700">
                        <MethodIcon className="w-4 h-4" />
                        {getMethodLabel(entry.deployment_method)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(entry.applied_at).toLocaleString('de-DE')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        {entry.rollback_available && entry.backup_id && (
                          <button
                            onClick={() => handleRollback(entry)}
                            className="text-yellow-600 hover:text-yellow-800 flex items-center gap-1"
                            title="Rückgängig machen"
                          >
                            <RotateCcw className="w-4 h-4" />
                            Rollback
                          </button>
                        )}
                        {!entry.success && entry.error_message && (
                          <button
                            onClick={() => setSelectedEntry(entry)}
                            className="text-red-600 hover:text-red-800"
                          >
                            Details
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Error Detail Modal */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Fehlerdetails</h3>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-red-800">{selectedEntry.error_message}</p>
            </div>
            <button
              onClick={() => setSelectedEntry(null)}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Schließen
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

