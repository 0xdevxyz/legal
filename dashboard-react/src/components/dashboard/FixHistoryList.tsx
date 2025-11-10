'use client'

import { useState, useEffect } from 'react'
import { Calendar, Download, FileText, Code, RefreshCw, Filter } from 'lucide-react'

interface GeneratedFix {
  id: number
  issue_id: string
  issue_category: string
  fix_type: string
  plan_type: string
  generated_at: string
  exported: boolean
  exported_at: string | null
  export_format: string | null
}

interface FixHistoryResponse {
  success: boolean
  fixes: GeneratedFix[]
  total: number
}

export function FixHistoryList() {
  const [fixes, setFixes] = useState<GeneratedFix[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'exported' | 'not_exported'>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  useEffect(() => {
    loadFixHistory()
  }, [])

  const loadFixHistory = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('https://api.complyo.tech/api/v2/fixes/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data: FixHistoryResponse = await response.json()
        setFixes(data.fixes)
      }
    } catch (error) {
      console.error('Failed to load fix history:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async (fixId: number, format: 'html' | 'pdf') => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('https://api.complyo.tech/api/v2/fixes/export', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          fix_id: fixId,
          export_format: format
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.download_url) {
          // Trigger download
          window.open(data.download_url, '_blank')
          // Reload history to update export status
          loadFixHistory()
        }
      }
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export fehlgeschlagen. Bitte versuchen Sie es erneut.')
    }
  }

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      'impressum': '📄',
      'datenschutz': '🔒',
      'cookies': '🍪',
      'barrierefreiheit': '♿',
      'agb': '📋',
      'widerrufsbelehrung': '↩️'
    }
    return icons[category.toLowerCase()] || '📝'
  }

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      'impressum': 'Impressum',
      'datenschutz': 'Datenschutz',
      'cookies': 'Cookie-Banner',
      'barrierefreiheit': 'Barrierefreiheit',
      'agb': 'AGB',
      'widerrufsbelehrung': 'Widerrufsbelehrung'
    }
    return labels[category.toLowerCase()] || category
  }

  const getFixTypeLabel = (fixType: string) => {
    const labels: Record<string, string> = {
      'code_snippet': 'Code-Snippet',
      'ai_personalized_fix': 'KI-Personalisiert',
      'full_document': 'Vollständiges Dokument'
    }
    return labels[fixType] || fixType
  }

  const getPlanBadge = (planType: string) => {
    if (planType === 'expert') {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          👔 Expert
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
        🤖 AI
      </span>
    )
  }

  // Filter Logic
  const categories = Array.from(new Set(fixes.map(f => f.issue_category)))
  
  const filteredFixes = fixes.filter(fix => {
    if (filter === 'exported' && !fix.exported) return false
    if (filter === 'not_exported' && fix.exported) return false
    if (categoryFilter !== 'all' && fix.issue_category !== categoryFilter) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500 mb-4" />
        <p className="text-gray-400">Lade Optimierungen...</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <FileText className="w-6 h-6" />
          Optimierungen meiner Webseite
        </h2>
        <button
          onClick={loadFixHistory}
          className="px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Aktualisieren
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-400">Filter:</span>
        </div>
        
        {/* Export Status Filter */}
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as typeof filter)}
          className="px-3 py-1 bg-gray-700 text-white rounded-md text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
        >
          <option value="all">Alle</option>
          <option value="exported">Exportiert</option>
          <option value="not_exported">Nicht exportiert</option>
        </select>

        {/* Category Filter */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-1 bg-gray-700 text-white rounded-md text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
        >
          <option value="all">Alle Kategorien</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {getCategoryLabel(cat)}
            </option>
          ))}
        </select>
      </div>

      {/* Fix List */}
      {filteredFixes.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">
            {fixes.length === 0 
              ? 'Noch keine Fixes generiert' 
              : 'Keine Fixes entsprechen den Filterkriterien'}
          </p>
          <p className="text-gray-500 text-sm">
            Generieren Sie Ihren ersten Fix in der Website-Analyse
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredFixes.map(fix => (
            <div
              key={fix.id}
              className="bg-gray-700 rounded-lg p-5 border border-gray-600 hover:border-blue-500 transition-colors"
            >
              <div className="flex items-start justify-between">
                {/* Left Side: Fix Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getCategoryIcon(fix.issue_category)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        {getCategoryLabel(fix.issue_category)}
                      </h3>
                      <p className="text-sm text-gray-400">
                        {getFixTypeLabel(fix.fix_type)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 text-sm text-gray-400 mt-3">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>{new Date(fix.generated_at).toLocaleDateString('de-DE', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}</span>
                    </div>
                    {getPlanBadge(fix.plan_type)}
                    {fix.exported && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ Exportiert
                      </span>
                    )}
                  </div>
                </div>

                {/* Right Side: Actions */}
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => handleExport(fix.id, 'html')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm flex items-center gap-2"
                    title="Als HTML exportieren"
                  >
                    <Download className="w-4 h-4" />
                    HTML
                  </button>
                  <button
                    onClick={() => handleExport(fix.id, 'pdf')}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm flex items-center gap-2"
                    title="Als PDF exportieren"
                  >
                    <Download className="w-4 h-4" />
                    PDF
                  </button>
                </div>
              </div>

              {/* Issue ID (for debugging/tracking) */}
              <div className="mt-3 pt-3 border-t border-gray-600">
                <p className="text-xs text-gray-500">
                  Fix-ID: #{fix.id} | Issue-ID: {fix.issue_id}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {fixes.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-700">
          <p className="text-sm text-gray-400 text-center">
            Gesamt: {fixes.length} Fix{fixes.length !== 1 ? 'es' : ''} generiert
            {filteredFixes.length !== fixes.length && (
              <span> | {filteredFixes.length} angezeigt</span>
            )}
          </p>
        </div>
      )}
    </div>
  )
}

