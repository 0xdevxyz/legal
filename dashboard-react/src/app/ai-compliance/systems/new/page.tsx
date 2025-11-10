'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Save, Sparkles } from 'lucide-react';
import { createAISystem } from '@/lib/ai-compliance-api';
import type { AISystemCreate } from '@/types/ai-compliance';

export default function NewAISystemPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<AISystemCreate>({
    name: '',
    description: '',
    vendor: '',
    purpose: '',
    domain: '',
    deployment_date: '',
    data_types: [],
    affected_persons: []
  });
  
  const domains = [
    { value: 'hr', label: 'Personal & HR' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'customer_service', label: 'Kundenservice' },
    { value: 'sales', label: 'Vertrieb' },
    { value: 'finance', label: 'Finanzen' },
    { value: 'operations', label: 'Operations' },
    { value: 'product', label: 'Produktentwicklung' },
    { value: 'other', label: 'Sonstiges' }
  ];
  
  const commonDataTypes = [
    'personal_data',
    'customer_data',
    'employee_data',
    'financial_data',
    'health_data',
    'biometric_data',
    'behavioral_data',
    'location_data'
  ];
  
  const commonAffectedPersons = [
    'customers',
    'employees',
    'job_applicants',
    'contractors',
    'suppliers',
    'minors',
    'public'
  ];
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.description || !formData.purpose) {
      setError('Bitte füllen Sie alle Pflichtfelder aus');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const system = await createAISystem(formData);
      
      // Redirect to system detail page
      router.push(`/ai-compliance/systems/${system.id}`);
    } catch (err: any) {
      console.error('Error creating AI system:', err);
      setError(err.response?.data?.detail || 'Fehler beim Erstellen des KI-Systems');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDataTypeToggle = (type: string) => {
    const current = formData.data_types || [];
    const updated = current.includes(type)
      ? current.filter(t => t !== type)
      : [...current, type];
    setFormData({ ...formData, data_types: updated });
  };
  
  const handleAffectedPersonToggle = (person: string) => {
    const current = formData.affected_persons || [];
    const updated = current.includes(person)
      ? current.filter(p => p !== person)
      : [...current, person];
    setFormData({ ...formData, affected_persons: updated });
  };
  
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Zurück
        </button>
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Neues KI-System hinzufügen
          </h1>
          <p className="text-gray-400">
            Registrieren Sie ein KI-System für die EU AI Act Compliance-Prüfung
          </p>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 space-y-4">
            <h2 className="text-xl font-semibold mb-4">Grundinformationen</h2>
            
            {/* Name */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Name des KI-Systems <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="z.B. ChatBot für Kundenservice"
                required
              />
            </div>
            
            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Beschreibung <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={3}
                placeholder="Kurze Beschreibung des KI-Systems und seiner Funktionsweise"
                required
              />
            </div>
            
            {/* Purpose */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Verwendungszweck <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.purpose}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                rows={3}
                placeholder="Wofür wird das KI-System eingesetzt? Welche Probleme löst es?"
                required
              />
            </div>
            
            {/* Vendor */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Anbieter/Hersteller
              </label>
              <input
                type="text"
                value={formData.vendor}
                onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="z.B. OpenAI, Google, Microsoft"
              />
            </div>
            
            {/* Domain */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Einsatzbereich
              </label>
              <select
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Bitte wählen...</option>
                {domains.map(d => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>
            
            {/* Deployment Date */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Deployment-Datum
              </label>
              <input
                type="date"
                value={formData.deployment_date}
                onChange={(e) => setFormData({ ...formData, deployment_date: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          
          {/* Data Types */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Verarbeitete Datentypen</h2>
            <p className="text-sm text-gray-400 mb-4">
              Welche Art von Daten verarbeitet das KI-System?
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {commonDataTypes.map(type => (
                <label
                  key={type}
                  className="flex items-center gap-2 p-3 bg-gray-700 border border-gray-600 rounded-lg cursor-pointer hover:border-purple-500 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={formData.data_types?.includes(type)}
                    onChange={() => handleDataTypeToggle(type)}
                    className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                  />
                  <span className="text-sm capitalize">
                    {type.replace(/_/g, ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Affected Persons */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Betroffene Personen</h2>
            <p className="text-sm text-gray-400 mb-4">
              Welche Personengruppen sind von diesem KI-System betroffen?
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {commonAffectedPersons.map(person => (
                <label
                  key={person}
                  className="flex items-center gap-2 p-3 bg-gray-700 border border-gray-600 rounded-lg cursor-pointer hover:border-purple-500 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={formData.affected_persons?.includes(person)}
                    onChange={() => handleAffectedPersonToggle(person)}
                    className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                  />
                  <span className="text-sm capitalize">
                    {person.replace(/_/g, ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Submit Button */}
          <div className="flex items-center gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Erstelle...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  KI-System erstellen
                </>
              )}
            </button>
            
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors font-medium"
            >
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

