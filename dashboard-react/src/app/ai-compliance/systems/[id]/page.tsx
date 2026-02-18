'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, RefreshCw, FileText, AlertTriangle, CheckCircle2, Clock, Download, Plus, Loader2, Trash2, Upload } from 'lucide-react';
import AIRiskBadge from '@/components/ai-compliance/AIRiskBadge';
import ComplianceProgress from '@/components/ai-compliance/ComplianceProgress';
import DocumentUpload from '@/components/ai-compliance/DocumentUpload';
import {
  getAISystem,
  getSystemScans,
  scanAISystem,
  getSystemDocumentation,
  generateDocumentation,
  listSystemDocuments,
  downloadDocumentation,
  deleteDocumentation,
  downloadUploadedFile,
  getDocumentTypeLabel,
  type DocumentType,
  type GeneratedDocument
} from '@/lib/ai-compliance-api';
import type { AISystem, ComplianceScan } from '@/types/ai-compliance';

export default function AISystemDetailPage() {
  const router = useRouter();
  const params = useParams();
  const systemId = params?.id as string;
  
  const [system, setSystem] = useState<AISystem | null>(null);
  const [scans, setScans] = useState<ComplianceScan[]>([]);
  const [documentation, setDocumentation] = useState<any>(null);
  const [generatedDocs, setGeneratedDocs] = useState<GeneratedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [generating, setGenerating] = useState<DocumentType | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'scans' | 'documentation'>('overview');
  
  useEffect(() => {
    loadSystemData();
  }, [systemId]);
  
  const loadSystemData = async () => {
    try {
      setLoading(true);
      
      const [systemData, scansData, docsData, generatedDocsData] = await Promise.all([
        getAISystem(systemId),
        getSystemScans(systemId, 10),
        getSystemDocumentation(systemId),
        listSystemDocuments(systemId).catch(() => ({ documents: [] }))
      ]);
      
      setSystem(systemData);
      setScans(scansData);
      setDocumentation(docsData);
      setGeneratedDocs(generatedDocsData.documents || []);
    } catch (err: any) {
      console.error('Error loading system:', err);
      alert('Fehler beim Laden: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };
  
  const handleScan = async () => {
    try {
      setScanning(true);
      await scanAISystem(systemId, true);
      await loadSystemData();
    } catch (err: any) {
      console.error('Error scanning:', err);
      alert('Fehler beim Scannen: ' + (err.response?.data?.detail || err.message));
    } finally {
      setScanning(false);
    }
  };
  
  const handleGenerateDoc = async (docType: DocumentType) => {
    try {
      setGenerating(docType);
      const result = await generateDocumentation(systemId, docType);
      if (result.success) {
        setGeneratedDocs(prev => [result.document, ...prev]);
        alert('Dokument erfolgreich generiert!');
      }
    } catch (err: any) {
      console.error('Error generating doc:', err);
      alert('Fehler beim Generieren: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(null);
    }
  };
  
  const handleDownloadDoc = async (docId: string, format: 'html' | 'pdf', title: string) => {
    try {
      setDownloading(docId);
      const blob = await downloadDocumentation(docId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Error downloading doc:', err);
      alert('Fehler beim Download: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDownloading(null);
    }
  };
  
  const handleDeleteDoc = async (docId: string, title: string) => {
    if (!confirm(`Dokument "${title}" wirklich löschen?`)) return;
    
    try {
      await deleteDocumentation(docId);
      setGeneratedDocs(prev => prev.filter(d => d.id !== docId));
      await loadSystemData();
    } catch (err: any) {
      console.error('Error deleting doc:', err);
      alert('Fehler beim Löschen: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  if (loading || !system) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-800 rounded w-64" />
            <div className="h-48 bg-gray-800 rounded" />
          </div>
        </div>
      </div>
    );
  }
  
  const latestScan = scans[0];
  
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Zurück zur Übersicht
        </button>
        
        {/* System Header */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{system.name}</h1>
              <p className="text-gray-400">{system.description}</p>
            </div>
            
            <div className="flex items-center gap-3">
              {system.risk_category && (
                <AIRiskBadge category={system.risk_category} size="lg" />
              )}
              
              <button
                onClick={handleScan}
                disabled={scanning}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${scanning ? 'animate-spin' : ''}`} />
                {scanning ? 'Scannt...' : 'Neu scannen'}
              </button>
            </div>
          </div>
          
          {/* System Metadata */}
          <div className="grid grid-cols-4 gap-4 pt-4 border-t border-gray-700">
            <div>
              <div className="text-sm text-gray-400 mb-1">Anbieter</div>
              <div className="font-medium">{system.vendor || 'Nicht angegeben'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Einsatzbereich</div>
              <div className="font-medium capitalize">{system.domain || 'Nicht angegeben'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Deployment</div>
              <div className="font-medium">
                {system.deployment_date 
                  ? new Date(system.deployment_date).toLocaleDateString('de-DE')
                  : 'Nicht angegeben'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Letzter Scan</div>
              <div className="font-medium">
                {system.last_assessment_date
                  ? new Date(system.last_assessment_date).toLocaleDateString('de-DE')
                  : 'Noch nicht gescannt'}
              </div>
            </div>
          </div>
        </div>
        
        {/* Compliance Score Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 flex items-center justify-center">
            <ComplianceProgress score={system.compliance_score} size="lg" />
          </div>
          
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 col-span-2">
            <h3 className="text-lg font-semibold mb-4">Risiko-Bewertung</h3>
            {system.risk_reasoning ? (
              <p className="text-gray-300 leading-relaxed">{system.risk_reasoning}</p>
            ) : (
              <p className="text-gray-400 italic">Noch keine Risiko-Bewertung durchgeführt. Starten Sie einen Scan.</p>
            )}
            {system.confidence_score && (
              <div className="mt-4 text-sm text-gray-400">
                Confidence Score: {(system.confidence_score * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </div>
        
        {/* Tabs */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
          <div className="border-b border-gray-700">
            <div className="flex">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-6 py-3 font-medium transition-colors ${
                  activeTab === 'overview'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                Übersicht
              </button>
              <button
                onClick={() => setActiveTab('scans')}
                className={`px-6 py-3 font-medium transition-colors ${
                  activeTab === 'scans'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                Scan-Historie ({scans.length})
              </button>
              <button
                onClick={() => setActiveTab('documentation')}
                className={`px-6 py-3 font-medium transition-colors ${
                  activeTab === 'documentation'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                Dokumentation
              </button>
            </div>
          </div>
          
          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && latestScan && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Compliance-Anforderungen</h3>
                  
                  {/* Requirements Met */}
                  {latestScan.requirements_met && latestScan.requirements_met.length > 0 && (
                    <div className="mb-6">
                      <h4 className="text-sm font-medium text-green-400 mb-3 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        Erfüllt ({latestScan.requirements_met.length})
                      </h4>
                      <div className="space-y-2">
                        {latestScan.requirements_met.map((req, idx) => (
                          <div key={idx} className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                            <div className="font-medium text-green-400">{req.requirement}</div>
                            {req.evidence && (
                              <div className="text-sm text-gray-400 mt-1">{req.evidence}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Requirements Failed */}
                  {latestScan.requirements_failed && latestScan.requirements_failed.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Nicht erfüllt ({latestScan.requirements_failed.length})
                      </h4>
                      <div className="space-y-2">
                        {latestScan.requirements_failed.map((req, idx) => (
                          <div key={idx} className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                            <div className="font-medium text-red-400">{req.requirement}</div>
                            {req.reason && (
                              <div className="text-sm text-gray-400 mt-1">{req.reason}</div>
                            )}
                            {req.severity && (
                              <span className={`inline-block mt-2 text-xs px-2 py-1 rounded ${
                                req.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                req.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                req.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                'bg-gray-500/20 text-gray-400'
                              }`}>
                                {req.severity.toUpperCase()}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Recommendations */}
                {latestScan.recommendations && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Empfehlungen</h3>
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <p className="text-gray-300 leading-relaxed whitespace-pre-line">
                        {latestScan.recommendations}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'overview' && !latestScan && (
              <div className="text-center py-12">
                <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">Noch kein Scan durchgeführt</h3>
                <p className="text-gray-400 mb-6">
                  Starten Sie einen Compliance-Scan, um detaillierte Ergebnisse zu sehen.
                </p>
                <button
                  onClick={handleScan}
                  disabled={scanning}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                >
                  {scanning ? 'Scannt...' : 'Ersten Scan starten'}
                </button>
              </div>
            )}
            
            {/* Scans Tab */}
            {activeTab === 'scans' && (
              <div className="space-y-4">
                {scans.map((scan) => (
                  <div key={scan.scan_id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <ComplianceProgress score={scan.compliance_score} size="sm" showLabel={false} />
                        <div>
                          <div className="font-medium">{scan.compliance_score}% Compliance</div>
                          <div className="text-sm text-gray-400">
                            {new Date(scan.created_at).toLocaleString('de-DE')}
                          </div>
                        </div>
                      </div>
                      <AIRiskBadge category={scan.risk_category} size="sm" />
                    </div>
                    {scan.recommendations && (
                      <p className="text-sm text-gray-400 line-clamp-2">{scan.recommendations}</p>
                    )}
                  </div>
                ))}
                
                {scans.length === 0 && (
                  <div className="text-center py-12 text-gray-400">
                    Noch keine Scans vorhanden
                  </div>
                )}
              </div>
            )}
            
            {/* Documentation Tab */}
            {activeTab === 'documentation' && documentation && (
              <div className="space-y-6">
                {/* Upload Section */}
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Dokumentation</h3>
                  <DocumentUpload systemId={systemId} onUploadComplete={loadSystemData} />
                </div>
                
                {/* Generate New Documents Section */}
                <div>
                  <h4 className="text-md font-medium text-gray-300 mb-4">Dokument automatisch generieren</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {(['risk_assessment', 'technical_documentation', 'conformity_declaration'] as DocumentType[]).map((docType) => (
                      <button
                        key={docType}
                        onClick={() => handleGenerateDoc(docType)}
                        disabled={generating !== null}
                        className="bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg p-4 text-left transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex items-center gap-3 mb-2">
                          {generating === docType ? (
                            <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                          ) : (
                            <Plus className="w-5 h-5 text-purple-400" />
                          )}
                          <span className="font-medium">{getDocumentTypeLabel(docType)}</span>
                        </div>
                        <p className="text-sm text-gray-400">
                          {docType === 'risk_assessment' && 'Risk Assessment Report nach Art. 9 AI Act'}
                          {docType === 'technical_documentation' && 'Technische Dokumentation nach Art. 11 AI Act'}
                          {docType === 'conformity_declaration' && 'EU-Konformitätserklärung nach Art. 47 AI Act'}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Generated Documents List */}
                {generatedDocs.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-gray-300 mb-4">Alle Dokumente ({generatedDocs.length})</h4>
                    <div className="space-y-3">
                      {generatedDocs.map((doc) => (
                        <div key={doc.id} className="bg-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <FileText className="w-5 h-5 text-purple-400" />
                              <div>
                                <div className="font-medium flex items-center gap-2">
                                  {doc.title}
                                  <span className={`text-xs px-2 py-0.5 rounded ${
                                    doc.status === 'uploaded' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'
                                  }`}>
                                    {doc.status === 'uploaded' ? 'Hochgeladen' : 'Generiert'}
                                  </span>
                                </div>
                                <div className="text-sm text-gray-400">
                                  Version {doc.version} • {new Date(doc.created_at).toLocaleDateString('de-DE')}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleDownloadDoc(doc.id, 'html', doc.title)}
                                disabled={downloading === doc.id}
                                className="flex items-center gap-1 px-3 py-1.5 bg-gray-600 hover:bg-gray-500 rounded text-sm transition-colors disabled:opacity-50"
                              >
                                {downloading === doc.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Download className="w-4 h-4" />
                                )}
                                HTML
                              </button>
                              <button
                                onClick={() => handleDownloadDoc(doc.id, 'pdf', doc.title)}
                                disabled={downloading === doc.id}
                                className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded text-sm transition-colors disabled:opacity-50"
                              >
                                {downloading === doc.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Download className="w-4 h-4" />
                                )}
                                PDF
                              </button>
                              <button
                                onClick={() => handleDeleteDoc(doc.id, doc.title)}
                                className="flex items-center gap-1 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded text-sm transition-colors"
                                title="Löschen"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Required Documentation */}
                <div>
                  <h4 className="text-md font-medium text-gray-300 mb-4">Erforderliche Dokumentation laut AI Act</h4>
                  <div className="space-y-3">
                    {documentation.required?.map((doc: any, idx: number) => (
                      <div key={idx} className="bg-gray-700 rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <FileText className="w-4 h-4 text-purple-400" />
                              <div className="font-medium">{doc.title}</div>
                              {doc.mandatory && (
                                <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded">
                                  Pflicht
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-400">{doc.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {documentation.existing && documentation.existing.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Hochgeladene Dokumente</h3>
                    <div className="space-y-2">
                      {documentation.existing.map((doc: any) => (
                        <div key={doc.id} className="bg-gray-700 rounded-lg p-3 flex items-center justify-between">
                          <div>
                            <div className="font-medium">{doc.title}</div>
                            <div className="text-sm text-gray-400">Version {doc.version} • {doc.status}</div>
                          </div>
                          <button className="text-purple-400 hover:text-purple-300 text-sm">
                            Ansehen
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
