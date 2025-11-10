'use client';

import React from 'react';
import { Shield, Download, CheckCircle, TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface AbmahnschutzStatusProps {
  score: number;
  lastScanDate?: string;
  hasERecht24Membership?: boolean;
  usesERecht24Texts?: boolean;
}

interface InfoBoxProps {
  icon: string;
  label: string;
  value: string;
  className?: string;
}

const InfoBox: React.FC<InfoBoxProps> = ({ icon, label, value, className = '' }) => (
  <div className={`bg-gray-800/50 rounded-lg p-4 ${className}`}>
    <div className="flex items-center gap-2 mb-2">
      <span className="text-2xl">{icon}</span>
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
    </div>
    <div className="text-lg font-bold text-white">{value}</div>
  </div>
);

export const AbmahnschutzStatus: React.FC<AbmahnschutzStatusProps> = ({
  score,
  lastScanDate,
  hasERecht24Membership = false,
  usesERecht24Texts = false
}) => {
  const isFullyProtected = score === 100 && hasERecht24Membership && usesERecht24Texts;
  const pointsRemaining = 100 - score;
  
  // Fortschrittsberechnung
  const progressPercentage = Math.min(score, 100);
  
  // Datum formatieren
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Noch nicht gescannt';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
      
      if (diffHours < 24) return `Vor ${diffHours}h`;
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `Vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`;
      return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return 'Ungültig';
    }
  };

  if (isFullyProtected) {
    // Vollständiger Abmahnschutz aktiv
    return (
      <Card className="bg-gradient-to-r from-green-900 to-emerald-900 border-2 border-green-500 shadow-lg mb-6">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-4">
            <div className="bg-green-500/20 p-3 rounded-xl border border-green-500">
              <Shield className="w-8 h-8 text-green-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                🛡️ Abmahnschutz AKTIV
                <CheckCircle className="w-6 h-6 text-green-400" />
              </h3>
              <p className="text-green-200 text-sm mt-1">
                Sie sind umfassend gegen Abmahnungen geschützt!
              </p>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <InfoBox 
              icon="✅" 
              label="Versicherungssumme" 
              value="50.000€"
              className="border border-green-500/30"
            />
            <InfoBox 
              icon="📋" 
              label="Rechtstexte" 
              value="eRecht24"
              className="border border-green-500/30"
            />
            <InfoBox 
              icon="🔄" 
              label="Letzter Scan" 
              value={formatDate(lastScanDate)}
              className="border border-green-500/30"
            />
            <InfoBox 
              icon="📡" 
              label="Updates" 
              value="Automatisch"
              className="border border-green-500/30"
            />
          </div>

          {/* Schutz-Details */}
          <div className="bg-green-950/50 rounded-lg p-4 mb-4 border border-green-500/30">
            <h4 className="text-sm font-semibold text-green-300 mb-3">Ihr Schutz umfasst:</h4>
            <ul className="space-y-2 text-sm text-green-100">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span>Abmahnungen wegen fehlerhaftem Impressum</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span>Datenschutzverstöße (DSGVO)</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span>Cookie-Consent-Probleme (TTDSG)</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span>Barrierefreiheit (BFSG ab 2025)</span>
              </li>
            </ul>
          </div>

          {/* Zertifikat-Download */}
          <Button 
            className="w-full bg-white text-green-900 hover:bg-green-50 font-semibold shadow-md transition-all"
            onClick={() => {
              // TODO: API-Call zum Zertifikat-Download
              alert('📥 Zertifikat-Download wird vorbereitet...\n\n(Feature wird im nächsten Schritt implementiert)');
            }}
          >
            <Download className="w-4 h-4 mr-2" />
            Abmahnschutz-Zertifikat herunterladen
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Abmahnschutz noch nicht aktiv - Fortschrittsanzeige
  return (
    <Card className="bg-gradient-to-r from-blue-900 to-purple-900 border-2 border-blue-500 shadow-lg mb-6">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-4">
          <div className="bg-blue-500/20 p-3 rounded-xl border border-blue-500">
            <Shield className="w-8 h-8 text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-2xl font-bold text-white flex items-center gap-2">
              ⏳ Abmahnschutz bei 100%
            </h3>
            <p className="text-blue-200 text-sm mt-1">
              {pointsRemaining > 0 
                ? `Noch ${pointsRemaining} Punkt${pointsRemaining > 1 ? 'e' : ''} bis zum vollständigen Schutz`
                : 'Fast geschafft! Aktivieren Sie den Abmahnschutz.'}
            </p>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Fortschrittsbalken */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-300">Compliance-Score</span>
            <span className="text-2xl font-bold text-white">
              {score}<span className="text-lg text-gray-400">/100</span>
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out flex items-center justify-end pr-2"
              style={{ width: `${progressPercentage}%` }}
            >
              {progressPercentage > 15 && (
                <TrendingUp className="w-3 h-3 text-white" />
              )}
            </div>
          </div>
        </div>

        {/* Voraussetzungen */}
        <div className="bg-blue-950/50 rounded-lg p-4 border border-blue-500/30">
          <h4 className="text-sm font-semibold text-blue-300 mb-3">Voraussetzungen für Abmahnschutz:</h4>
          <ul className="space-y-2 text-sm">
            <li className={`flex items-start gap-2 ${score === 100 ? 'text-green-300' : 'text-gray-300'}`}>
              {score === 100 ? (
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              ) : (
                <div className="w-4 h-4 border-2 border-gray-500 rounded-full mt-0.5 flex-shrink-0" />
              )}
              <span>100% Compliance-Score erreichen {score === 100 && '✓'}</span>
            </li>
            <li className={`flex items-start gap-2 ${hasERecht24Membership ? 'text-green-300' : 'text-gray-300'}`}>
              {hasERecht24Membership ? (
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              ) : (
                <div className="w-4 h-4 border-2 border-gray-500 rounded-full mt-0.5 flex-shrink-0" />
              )}
              <span>eRecht24 Premium-Mitgliedschaft {hasERecht24Membership && '✓'}</span>
            </li>
            <li className={`flex items-start gap-2 ${usesERecht24Texts ? 'text-green-300' : 'text-gray-300'}`}>
              {usesERecht24Texts ? (
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              ) : (
                <div className="w-4 h-4 border-2 border-gray-500 rounded-full mt-0.5 flex-shrink-0" />
              )}
              <span>eRecht24-Rechtstexte verwenden {usesERecht24Texts && '✓'}</span>
            </li>
            <li className="flex items-start gap-2 text-gray-300">
              <div className="w-4 h-4 border-2 border-gray-500 rounded-full mt-0.5 flex-shrink-0" />
              <span>Regelmäßige Re-Scans (monatlich)</span>
            </li>
          </ul>
        </div>

        {/* Call-to-Action */}
        {score < 100 && (
          <div className="mt-4 p-4 bg-purple-900/30 rounded-lg border border-purple-500/30">
            <p className="text-sm text-purple-200 mb-3">
              💡 <strong>Tipp:</strong> Nutzen Sie unsere KI-Optimierung, um schnell 100% zu erreichen!
            </p>
            <Button 
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              onClick={() => {
                // Scroll to KI-Optimierung Section
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              🤖 Jetzt mit KI auf 100% optimieren
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

