'use client';

import React, { useState } from 'react';
import { X, Server, Globe, GitBranch, Download, Shield, AlertTriangle, CheckCircle, Loader } from 'lucide-react';
import { ClientOnlyPortal } from '../ClientOnlyPortal';

interface ApplyFixModalProps {
  isOpen: boolean;
  onClose: () => void;
  fixId: string;
  fixTitle: string;
  fixCode: string;
  fixCategory: string;
  fixType: string;
}

type DeploymentMethod = 'ftp' | 'sftp' | 'github_pr' | 'zip_download';
type Step = 'method' | 'credentials' | 'backup' | 'confirm' | 'deploying' | 'success' | 'error';

interface DeploymentCredentials {
  host?: string;
  port?: string;
  username?: string;
  password?: string;
  path?: string;
  repo?: string;
  token?: string;
}

export const ApplyFixModal: React.FC<ApplyFixModalProps> = ({
  isOpen,
  onClose,
  fixId,
  fixTitle,
  fixCode,
  fixCategory,
  fixType
}) => {
  const [currentStep, setCurrentStep] = useState<Step>('method');
  const [selectedMethod, setSelectedMethod] = useState<DeploymentMethod>('zip_download');
  const [credentials, setCredentials] = useState<DeploymentCredentials>({});
  const [createBackup, setCreateBackup] = useState(true);
  const [userConfirmed, setUserConfirmed] = useState(false);
  const [deploymentResult, setDeploymentResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const deploymentMethods = [
    {
      id: 'zip_download' as DeploymentMethod,
      name: 'ZIP Download',
      description: 'Herunterladen und manuell deployen',
      icon: Download,
      isPremium: false,
      difficulty: 'Einfach'
    },
    {
      id: 'ftp' as DeploymentMethod,
      name: 'FTP Upload',
      description: 'Automatisch via FTP hochladen',
      icon: Server,
      isPremium: false,
      difficulty: 'Mittel'
    },
    {
      id: 'github_pr' as DeploymentMethod,
      name: 'GitHub Pull Request',
      description: 'PR erstellen für Review',
      icon: GitBranch,
      isPremium: false,
      difficulty: 'Fortgeschritten'
    },
    {
      id: 'sftp' as DeploymentMethod,
      name: 'SFTP/SSH',
      description: 'Sicherer SSH-Upload',
      icon: Shield,
      isPremium: true,
      difficulty: 'Fortgeschritten'
    }
  ];

  const handleMethodSelect = (method: DeploymentMethod) => {
    setSelectedMethod(method);
    setCurrentStep('credentials');
  };

  const handleCredentialsSubmit = () => {
    if (selectedMethod === 'zip_download') {
      // Für ZIP-Download direkt downloaden
      handleZipDownload();
    } else {
      setCurrentStep('backup');
    }
  };

  const handleBackupConfirm = () => {
    setCurrentStep('confirm');
  };

  const handleFinalConfirm = async () => {
    if (!userConfirmed) {
      alert('Bitte bestätigen Sie, dass Sie die Änderungen verstanden haben.');
      return;
    }

    setCurrentStep('deploying');
    
    try {
      // API-Call zum Anwenden des Fixes
      const response = await fetch('/api/v2/fixes/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          fix_id: fixId,
          deployment_method: selectedMethod,
          credentials,
          target_path: credentials.path || '/',
          backup_before_deploy: createBackup,
          user_confirmed: true,
          fix_category: fixCategory,
          fix_type: fixType
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setDeploymentResult(result);
        setCurrentStep('success');
      } else {
        setError(result.error || 'Deployment fehlgeschlagen');
        setCurrentStep('error');
      }
    } catch (err: any) {
      setError(err.message || 'Netzwerkfehler');
      setCurrentStep('error');
    }
  };

  const handleZipDownload = () => {
    // Erstelle Blob und trigger Download
    const blob = new Blob([fixCode], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `complyo-fix-${fixId}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    setCurrentStep('success');
    setDeploymentResult({ success: true, deployment_method: 'zip_download' });
  };

  const resetModal = () => {
    setCurrentStep('method');
    setSelectedMethod('zip_download');
    setCredentials({});
    setCreateBackup(true);
    setUserConfirmed(false);
    setDeploymentResult(null);
    setError(null);
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <ClientOnlyPortal>
      <div
        className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center p-4 z-[99999]"
        onClick={(e) => {
          if (e.target === e.currentTarget) handleClose();
        }}
      >
        <div
          className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Fix anwenden</h2>
              <p className="text-sm text-gray-600 mt-1">{fixTitle}</p>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Step: Method Selection */}
            {currentStep === 'method' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Wählen Sie eine Deployment-Methode:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {deploymentMethods.map((method) => (
                    <button
                      key={method.id}
                      onClick={() => handleMethodSelect(method.id)}
                      disabled={method.isPremium}
                      className={`p-4 border-2 rounded-lg text-left transition-all hover:shadow-lg ${
                        method.isPremium
                          ? 'border-gray-300 bg-gray-50 opacity-50 cursor-not-allowed'
                          : 'border-blue-300 hover:border-blue-500'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <method.icon className="w-6 h-6 text-blue-600 flex-shrink-0" />
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900">
                            {method.name}
                            {method.isPremium && (
                              <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                                Premium
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{method.description}</p>
                          <p className="text-xs text-gray-500 mt-2">Schwierigkeit: {method.difficulty}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step: Credentials */}
            {currentStep === 'credentials' && selectedMethod !== 'zip_download' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Zugangsdaten eingeben:</h3>
                
                {selectedMethod === 'ftp' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">FTP Host</label>
                      <input
                        type="text"
                        placeholder="ftp.beispiel.de"
                        value={credentials.host || ''}
                        onChange={(e) => setCredentials({ ...credentials, host: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                        <input
                          type="text"
                          placeholder="21"
                          value={credentials.port || '21'}
                          onChange={(e) => setCredentials({ ...credentials, port: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Pfad</label>
                        <input
                          type="text"
                          placeholder="/public_html"
                          value={credentials.path || ''}
                          onChange={(e) => setCredentials({ ...credentials, path: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Benutzername</label>
                      <input
                        type="text"
                        value={credentials.username || ''}
                        onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Passwort</label>
                      <input
                        type="password"
                        value={credentials.password || ''}
                        onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                {selectedMethod === 'github_pr' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">GitHub Repository</label>
                      <input
                        type="text"
                        placeholder="username/repo-name"
                        value={credentials.repo || ''}
                        onChange={(e) => setCredentials({ ...credentials, repo: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Personal Access Token</label>
                      <input
                        type="password"
                        placeholder="ghp_..."
                        value={credentials.token || ''}
                        onChange={(e) => setCredentials({ ...credentials, token: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        <a
                          href="https://github.com/settings/tokens"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          Token erstellen →
                        </a>
                      </p>
                    </div>
                  </div>
                )}

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setCurrentStep('method')}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={handleCredentialsSubmit}
                    disabled={!credentials.host && !credentials.repo}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Weiter
                  </button>
                </div>
              </div>
            )}

            {/* Step: Backup */}
            {currentStep === 'backup' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Backup-Optionen:</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-blue-900">Sicherheits-Empfehlung</h4>
                      <p className="text-sm text-blue-800 mt-1">
                        Wir empfehlen dringend, vor jeder Änderung ein Backup zu erstellen.
                        So können Sie Änderungen jederzeit rückgängig machen.
                      </p>
                    </div>
                  </div>
                </div>
                
                <label className="flex items-start gap-3 p-4 border-2 border-green-300 rounded-lg cursor-pointer hover:bg-green-50">
                  <input
                    type="checkbox"
                    checked={createBackup}
                    onChange={(e) => setCreateBackup(e.target.checked)}
                    className="mt-1 w-5 h-5 text-green-600"
                  />
                  <div>
                    <div className="font-semibold text-gray-900">Backup erstellen (empfohlen)</div>
                    <p className="text-sm text-gray-600 mt-1">
                      Speichert den aktuellen Zustand für 30 Tage. Rollback jederzeit möglich.
                    </p>
                  </div>
                </label>

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setCurrentStep('credentials')}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={handleBackupConfirm}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Weiter
                  </button>
                </div>
              </div>
            )}

            {/* Step: Final Confirmation */}
            {currentStep === 'confirm' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Bestätigung erforderlich:</h3>
                
                <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-yellow-900">Rechtlicher Hinweis</h4>
                      <p className="text-sm text-yellow-800 mt-1">
                        Complyo generiert Patches basierend auf öffentlich zugänglichem Code. 
                        Sie übernehmen die Verantwortung für die Anwendung dieser Änderungen in Ihrem System.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <h4 className="font-semibold mb-2">Zusammenfassung:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Methode: <strong>{deploymentMethods.find(m => m.id === selectedMethod)?.name}</strong></li>
                    <li>• Backup: <strong>{createBackup ? 'Ja (30 Tage)' : 'Nein'}</strong></li>
                    <li>• Fix-Kategorie: <strong>{fixCategory}</strong></li>
                  </ul>
                </div>

                <label className="flex items-start gap-3 cursor-pointer mb-4">
                  <input
                    type="checkbox"
                    checked={userConfirmed}
                    onChange={(e) => setUserConfirmed(e.target.checked)}
                    className="mt-1 w-5 h-5 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">
                    Ich bestätige, dass ich die Änderungen verstanden habe und die Verantwortung übernehme.
                  </span>
                </label>

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setCurrentStep('backup')}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={handleFinalConfirm}
                    disabled={!userConfirmed}
                    className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 font-semibold"
                  >
                    Jetzt anwenden
                  </button>
                </div>
              </div>
            )}

            {/* Step: Deploying */}
            {currentStep === 'deploying' && (
              <div className="text-center py-8">
                <Loader className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Fix wird angewendet...</h3>
                <p className="text-gray-600">Bitte warten Sie einen Moment.</p>
              </div>
            )}

            {/* Step: Success */}
            {currentStep === 'success' && (
              <div className="text-center py-8">
                <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Erfolgreich!</h3>
                {deploymentResult && (
                  <div className="text-left bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                    {deploymentResult.backup_created && (
                      <p className="text-sm text-green-800 mb-2">
                        ✅ Backup erstellt: <strong>{deploymentResult.backup_id}</strong>
                      </p>
                    )}
                    {deploymentResult.files_deployed && (
                      <p className="text-sm text-green-800">
                        📁 Dateien deployt: <strong>{deploymentResult.files_deployed.length}</strong>
                      </p>
                    )}
                  </div>
                )}
                <button
                  onClick={handleClose}
                  className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Schließen
                </button>
              </div>
            )}

            {/* Step: Error */}
            {currentStep === 'error' && (
              <div className="text-center py-8">
                <AlertTriangle className="w-16 h-16 text-red-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Fehler aufgetreten</h3>
                {error && (
                  <div className="text-left bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
                <div className="mt-6 flex gap-3 justify-center">
                  <button
                    onClick={() => setCurrentStep('confirm')}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Erneut versuchen
                  </button>
                  <button
                    onClick={handleClose}
                    className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Abbrechen
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ClientOnlyPortal>
  );
};

