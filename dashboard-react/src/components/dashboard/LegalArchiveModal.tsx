'use client';

import React, { useState, useEffect } from 'react';
import { 
  X, Archive, ChevronLeft, ChevronRight, Filter, Search, 
  AlertTriangle, Info, Clock, TrendingUp 
} from 'lucide-react';

interface LegalUpdate {
  id: number;
  update_type: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  action_required: boolean;
  published_at: string;
  effective_date?: string;
  url?: string;
  classification?: {
    impact_score?: number;
    confidence?: string;
  };
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const LegalArchiveModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [updates, setUpdates] = useState<LegalUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    if (isOpen) {
      loadArchive();
    }
  }, [isOpen, page, filterSeverity]);
  
  const loadArchive = async () => {
    setIsLoading(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      
      let url = `${API_URL}/api/legal-ai/archive?page=${page}&page_size=20`;
      if (filterSeverity) {
        url += `&severity=${filterSeverity}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUpdates(data.updates);
        setTotalPages(Math.ceil(data.total / 20));
      }
    } catch (error) {
      console.error('❌ Fehler beim Laden des Archivs:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', { 
      day: '2-digit', 
      month: 'long', 
      year: 'numeric' 
    });
  };
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/10 border-red-500';
      case 'warning': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500';
      default: return 'text-blue-400 bg-blue-500/10 border-blue-500';
    }
  };
  
  if (!isOpen) return null;
  
  const filteredUpdates = searchTerm
    ? updates.filter(u => 
        u.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : updates;
  
  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="bg-gray-900 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden shadow-2xl border-2 border-purple-500/30"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700 bg-gradient-to-r from-purple-900/40 to-blue-900/40">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <Archive className="w-7 h-7 text-purple-400" />
              Gesetzesänderungen-Archiv
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              Ältere Änderungen und bereits umgesetzte Updates
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
        </div>
        
        {/* Filter & Search */}
        <div className="p-4 border-b border-gray-700 bg-gray-800/50">
          <div className="flex flex-col md:flex-row gap-3">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <label htmlFor="legal-archive-search" className="sr-only">Rechtsänderungen durchsuchen</label>
              <input
                type="text"
                id="legal-archive-search"
                placeholder="Suche nach Titel oder Beschreibung..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                aria-label="Rechtsänderungen nach Titel oder Beschreibung durchsuchen"
                className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 text-sm"
              />
            </div>
            
            {/* Severity Filter */}
            <div className="flex gap-2">
              <button
                onClick={() => setFilterSeverity('')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                  filterSeverity === '' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Alle
              </button>
              <button
                onClick={() => setFilterSeverity('critical')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                  filterSeverity === 'critical' 
                    ? 'bg-red-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Kritisch
              </button>
              <button
                onClick={() => setFilterSeverity('warning')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                  filterSeverity === 'warning' 
                    ? 'bg-yellow-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Warnung
              </button>
              <button
                onClick={() => setFilterSeverity('info')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                  filterSeverity === 'info' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Info
              </button>
            </div>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-250px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
            </div>
          ) : filteredUpdates.length > 0 ? (
            <div className="space-y-3">
              {filteredUpdates.map((update) => (
                <div
                  key={update.id}
                  className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 hover:shadow-lg transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className={`px-2 py-1 rounded text-xs font-bold border ${getSeverityColor(update.severity)}`}>
                          {update.severity.toUpperCase()}
                        </span>
                        {update.classification?.confidence && (
                          <span className="px-2 py-1 rounded text-xs font-semibold bg-green-500/20 text-green-400">
                            🤖 KI: {update.classification.confidence}
                          </span>
                        )}
                        {update.classification?.impact_score && (
                          <span className="px-2 py-1 rounded text-xs font-semibold bg-orange-500/20 text-orange-400">
                            Impact: {update.classification.impact_score.toFixed(1)}/10
                          </span>
                        )}
                      </div>
                      
                      <h3 className="text-white font-bold text-base mb-2">
                        {update.title}
                      </h3>
                      
                      <p className="text-gray-400 text-sm mb-3 leading-relaxed">
                        {update.description.substring(0, 200)}
                        {update.description.length > 200 && '...'}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(update.published_at)}
                        </span>
                        {update.effective_date && (
                          <span>
                            Gilt ab: {formatDate(update.effective_date)}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {update.action_required && (
                      <div className="flex-shrink-0">
                        <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500">
                          Aktion erforderlich
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Archive className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">
                {searchTerm ? 'Keine Ergebnisse gefunden' : 'Keine archivierten Updates vorhanden'}
              </p>
            </div>
          )}
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-gray-700 bg-gray-800/50">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Zurück
            </button>
            
            <span className="text-gray-400 text-sm">
              Seite {page} von {totalPages}
            </span>
            
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              Weiter
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

