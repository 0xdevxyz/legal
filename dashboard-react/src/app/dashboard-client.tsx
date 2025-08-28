'use client'

import React, { useState } from 'react'
import { Search, AlertTriangle, CheckCircle, AlertCircle, Globe, RefreshCw, Bot, UserCheck } from 'lucide-react'

interface ComplianceResult {
  category: string
  status: 'pass' | 'fail' | 'warning'
  score: number
  message: string
  details?: any
}

interface AnalysisData {
  url: string
  overall_score: number
  total_issues: number
  critical_issues: number
  results: ComplianceResult[]
  scan_timestamp: string
  scan_duration_ms: number
}

export default function DashboardClient() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!url.trim()) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech'
      console.log('Sending request to:', `${apiUrl}/api/analyze`)
      
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('Analysis result:', data)
      setAnalysisData(data)
    } catch (err) {
      console.error('Analysis error:', err)
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler')
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'fail':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Complyo Dashboard
          </h1>
          <p className="text-gray-400 mt-2">KI-gestützte Website-Compliance für Deutschland</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* URL Input Section */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">
            <div className="flex-1 w-full">
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Website-URL eingeben (z.B. example.com)"
                  className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                />
              </div>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !url.trim()}
              className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="h-5 w-5 animate-spin" />
                  <span>Analysiere...</span>
                </>
              ) : (
                <>
                  <Search className="h-5 w-5" />
                  <span>Analysieren</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-8">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="text-red-200">Fehler: {error}</span>
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysisData && (
          <div className="space-y-6">
            
            {/* Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Analysierte Website</h3>
                <p className="text-lg font-bold text-white mt-2 truncate" title={analysisData.url}>
                  {analysisData.url}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Gesamt-Score</h3>
                <p className={`text-2xl font-bold mt-2 ${getScoreColor(analysisData.overall_score)}`}>
                  {Math.round(analysisData.overall_score)}/100
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Gefundene Issues</h3>
                <p className="text-2xl font-bold text-white mt-2">{analysisData.total_issues || 0}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-400">Kritische Issues</h3>
                <p className="text-2xl font-bold text-red-500 mt-2">{analysisData.critical_issues || 0}</p>
              </div>
            </div>

            {/* Detailed Results */}
            {analysisData.results && analysisData.results.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-xl font-bold text-white mb-6">
                  Gefundene Issues ({analysisData.results.length})
                </h2>
                
                <div className="space-y-4">
                  {analysisData.results.map((result, index) => (
                    <div key={index} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3 flex-1">
                          {getStatusIcon(result.status)}
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-semibold text-white">
                              {result.category}
                            </h3>
                            <p className="text-gray-300 mt-1 break-words">
                              {result.message}
                            </p>
                            {result.details && (
                              <div className="mt-2 text-sm text-gray-400">
                                <details className="cursor-pointer">
                                  <summary className="hover:text-gray-300">Details anzeigen</summary>
                                  <pre className="mt-2 whitespace-pre-wrap text-xs bg-gray-800 p-2 rounded overflow-x-auto">
                                    {JSON.stringify(result.details, null, 2)}
                                  </pre>
                                </details>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-4 flex-shrink-0">
                          <span className={`text-lg font-bold ${getScoreColor(result.score)}`}>
                            {Math.round(result.score)}%
                          </span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm">
                          <Bot className="h-4 w-4" />
                          <span>KI-Fix starten</span>
                        </button>
                        <button className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm">
                          <UserCheck className="h-4 w-4" />
                          <span>Experten-Beratung</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scan Info */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Scan-Details</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Scan-Zeitstempel:</span>
                  <p className="text-white mt-1">{analysisData.scan_timestamp}</p>
                </div>
                <div>
                  <span className="text-gray-400">Scan-Dauer:</span>
                  <p className="text-white mt-1">{analysisData.scan_duration_ms}ms</p>
                </div>
              </div>
            </div>

          </div>
        )}

        {/* Welcome Message (when no analysis) */}
        {!analysisData && !isLoading && (
          <div className="text-center py-12">
            <Globe className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Bereit für Ihre erste Analyse?</h2>
            <p className="text-gray-400 mb-6">
              Geben Sie eine Website-URL ein, um eine umfassende Compliance-Prüfung zu starten.
            </p>
            <div className="text-sm text-gray-500">
              <p>Beispiele: github.com, google.com, example.com</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
