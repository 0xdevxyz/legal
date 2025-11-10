'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Sparkles, TrendingUp, Shield, Clock } from 'lucide-react';
import AISystemCard from '@/components/ai-compliance/AISystemCard';
import ComplianceProgress from '@/components/ai-compliance/ComplianceProgress';
import {
  getAISystems,
  getAIComplianceStats,
  scanAISystem
} from '@/lib/ai-compliance-api';
import type { AISystem, AIComplianceStats } from '@/types/ai-compliance';

export default function AICompliancePage() {
  const router = useRouter();
  const [systems, setSystems] = useState<AISystem[]>([]);
  const [stats, setStats] = useState<AIComplianceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [systemsData, statsData] = await Promise.all([
        getAISystems(),
        getAIComplianceStats()
      ]);
      
      setSystems(systemsData);
      setStats(statsData);
    } catch (err: any) {
      console.error('Error loading AI systems:', err);
      setError(err.response?.data?.detail || 'Fehler beim Laden der Daten');
      
      // Check if user needs ComploAI Guard
      if (err.response?.status === 403) {
        router.push('/ai-compliance/upgrade');
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleScan = async (systemId: string) => {
    try {
      setScanning(systemId);
      await scanAISystem(systemId, true);
      
      // Reload data after scan
      await loadData();
    } catch (err: any) {
      console.error('Error scanning system:', err);
      alert('Fehler beim Scannen: ' + (err.response?.data?.detail || err.message));
    } finally {
      setScanning(null);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-800 rounded w-64" />
            <div className="grid grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-800 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              AI Compliance Dashboard
            </h1>
            <p className="text-gray-400">
              EU AI Act Compliance für Ihre KI-Systeme
            </p>
          </div>
          
          <button
            onClick={() => router.push('/ai-compliance/systems/new')}
            className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors font-medium"
          >
            <Plus className="w-5 h-5" />
            KI-System hinzufügen
          </button>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}
        
        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {/* Total Systems */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Sparkles className="w-6 h-6 text-purple-400" />
                </div>
                <span className="text-3xl font-bold">{stats.total_systems}</span>
              </div>
              <div className="text-sm text-gray-400">KI-Systeme</div>
            </div>
            
            {/* Average Compliance */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <Shield className="w-6 h-6 text-green-400" />
                </div>
                <span className="text-3xl font-bold">{stats.average_compliance_score}%</span>
              </div>
              <div className="text-sm text-gray-400">Ø Compliance</div>
            </div>
            
            {/* Scans Last 30 Days */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-blue-400" />
                </div>
                <span className="text-3xl font-bold">{stats.scans_last_30_days}</span>
              </div>
              <div className="text-sm text-gray-400">Scans (30 Tage)</div>
            </div>
            
            {/* Risk Distribution */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <Clock className="w-6 h-6 text-orange-400" />
                </div>
                <span className="text-3xl font-bold">
                  {stats.risk_distribution?.high || 0}
                </span>
              </div>
              <div className="text-sm text-gray-400">Hochrisiko-Systeme</div>
            </div>
          </div>
        )}
        
        {/* Systems List */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Ihre KI-Systeme</h2>
          
          {systems.length === 0 ? (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
              <Sparkles className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">
                Noch keine KI-Systeme registriert
              </h3>
              <p className="text-gray-400 mb-6">
                Fügen Sie Ihr erstes KI-System hinzu, um mit der Compliance-Prüfung zu beginnen.
              </p>
              <button
                onClick={() => router.push('/ai-compliance/systems/new')}
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors font-medium"
              >
                <Plus className="w-5 h-5" />
                Erstes KI-System hinzufügen
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {systems.map((system) => (
                <AISystemCard
                  key={system.id}
                  system={system}
                  onScan={handleScan}
                />
              ))}
            </div>
          )}
        </div>
        
        {/* Risk Distribution Chart */}
        {stats && stats.total_systems > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Risiko-Verteilung</h3>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(stats.risk_distribution || {}).map(([category, count]) => (
                <div key={category} className="text-center">
                  <div className="text-2xl font-bold mb-1">{count}</div>
                  <div className="text-sm text-gray-400 capitalize">{category}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

