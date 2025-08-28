'use client';

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Mail, 
  FileText, 
  TrendingUp, 
  Shield, 
  Database,
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2,
  RefreshCw
} from 'lucide-react';

interface DashboardStats {
  total_leads: number;
  verified_leads: number;
  converted_leads: number;
  leads_last_24h: number;
  verification_rate: number;
  conversion_rate: number;
  gdpr_compliant: boolean;
  data_retention_days: number;
  storage_type: string;
}

interface Lead {
  id: string;
  email: string;
  name: string;
  company?: string;
  status: string;
  email_verified: boolean;
  created_at: string;
  verified_at?: string;
  url_analyzed?: string;
}

interface AdminOverview {
  overview: DashboardStats;
  lead_sources: Record<string, number>;
  recent_activity: number;
  status_breakdown: Record<string, number>;
  system_status: {
    storage_type: string;
    gdpr_compliant: boolean;
    email_service: string;
    pdf_generation: string;
  };
}

const AdminDashboard: React.FC = () => {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
  const ADMIN_API_KEY = 'admin_complyo_2025';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load overview
      const overviewResponse = await fetch(
        `${API_BASE}/api/admin/dashboard/overview?api_key=${ADMIN_API_KEY}`
      );
      if (overviewResponse.ok) {
        const overviewData = await overviewResponse.json();
        setOverview(overviewData);
      }
      
      // Load leads
      const leadsResponse = await fetch(
        `${API_BASE}/api/admin/leads?api_key=${ADMIN_API_KEY}&limit=50`
      );
      if (leadsResponse.ok) {
        const leadsData = await leadsResponse.json();
        setLeads(leadsData.leads);
      }
      
    } catch (err) {
      setError('Fehler beim Laden der Dashboard-Daten');
      console.error('Dashboard loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async (leadId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/admin/leads/${leadId}/resend-verification?api_key=${ADMIN_API_KEY}`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        alert('Verification E-Mail wurde erneut gesendet');
        loadDashboardData(); // Reload data
      } else {
        alert('Fehler beim Senden der E-Mail');
      }
    } catch (err) {
      alert('Fehler beim Senden der E-Mail');
    }
  };

  const deleteLead = async (leadId: string) => {
    if (!confirm('Lead wirklich löschen? (DSGVO-Recht auf Löschung)')) {
      return;
    }
    
    const reason = prompt('Grund für die Löschung:') || 'Admin deletion';
    
    try {
      const response = await fetch(
        `${API_BASE}/api/admin/leads/${leadId}?api_key=${ADMIN_API_KEY}&reason=${encodeURIComponent(reason)}`,
        { method: 'DELETE' }
      );
      
      if (response.ok) {
        alert('Lead wurde gelöscht');
        loadDashboardData(); // Reload data
      } else {
        alert('Fehler beim Löschen');
      }
    } catch (err) {
      alert('Fehler beim Löschen');
    }
  };

  const getStatusBadge = (status: string, verified: boolean) => {
    if (status === 'converted') {
      return <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">Konvertiert</span>;
    } else if (verified) {
      return <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">Verifiziert</span>;
    } else {
      return <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs">Ausstehend</span>;
    }
  };

  const filteredLeads = selectedStatus === 'all' 
    ? leads 
    : leads.filter(lead => {
        if (selectedStatus === 'verified') return lead.email_verified;
        if (selectedStatus === 'unverified') return !lead.email_verified;
        if (selectedStatus === 'converted') return lead.status === 'converted';
        return true;
      });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Laden der Admin-Daten...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadDashboardData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🛡️ Complyo Admin Dashboard</h1>
              <p className="text-gray-600">GDPR-konforme Lead-Verwaltung</p>
            </div>
            <button 
              onClick={loadDashboardData}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Aktualisieren</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {overview && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Gesamt Leads</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.overview.total_leads}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Verifiziert</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.overview.verified_leads}</p>
                  <p className="text-xs text-green-600">{overview.overview.verification_rate}% Rate</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <FileText className="w-8 h-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Reports Gesendet</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.overview.converted_leads}</p>
                  <p className="text-xs text-purple-600">{overview.overview.conversion_rate}% Rate</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Heute</p>
                  <p className="text-2xl font-bold text-gray-900">{overview.overview.leads_last_24h}</p>
                  <p className="text-xs text-orange-600">Neue Leads</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* System Status */}
        {overview && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3">
                  <Database className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium">Datenbank</p>
                    <p className="text-xs text-gray-600 capitalize">{overview.system_status.storage_type}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Mail className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">E-Mail Service</p>
                    <p className="text-xs text-gray-600 capitalize">{overview.system_status.email_service}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-purple-600" />
                  <div>
                    <p className="text-sm font-medium">GDPR Status</p>
                    <p className="text-xs text-green-600">
                      {overview.system_status.gdpr_compliant ? 'Konform' : 'Nicht konform'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Leads Management */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Lead-Verwaltung</h2>
              <div className="flex space-x-2">
                <select 
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="border border-gray-300 rounded px-3 py-1 text-sm"
                >
                  <option value="all">Alle Status</option>
                  <option value="verified">Verifiziert</option>
                  <option value="unverified">Nicht verifiziert</option>
                  <option value="converted">Konvertiert</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lead</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Erstellt</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">URL</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Aktionen</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{lead.name}</div>
                        <div className="text-sm text-gray-500">{lead.email}</div>
                        {lead.company && (
                          <div className="text-xs text-gray-400">{lead.company}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(lead.status, lead.email_verified)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(lead.created_at).toLocaleDateString('de-DE')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.url_analyzed || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        {!lead.email_verified && (
                          <button
                            onClick={() => resendVerification(lead.id)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Verification E-Mail erneut senden"
                          >
                            <Mail className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteLead(lead.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Lead löschen (GDPR)"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredLeads.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">Keine Leads gefunden für den ausgewählten Filter.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;