'use client';

import Link from 'next/link';
import { Calendar, Building2, Scan, FileText, AlertCircle } from 'lucide-react';
import AIRiskBadge from './AIRiskBadge';
import ComplianceProgress from './ComplianceProgress';
import type { AISystem } from '@/types/ai-compliance';

interface AISystemCardProps {
  system: AISystem;
  onScan?: (systemId: string) => void;
  onDelete?: (systemId: string) => void;
}

export default function AISystemCard({ system, onScan, onDelete }: AISystemCardProps) {
  const isNew = !system.last_assessment_date;
  
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 hover:border-purple-500/50 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Link
            href={`/ai-compliance/systems/${system.id}`}
            className="text-lg font-semibold text-white hover:text-purple-400 transition-colors"
          >
            {system.name}
          </Link>
          <p className="text-sm text-gray-400 mt-1 line-clamp-2">
            {system.description}
          </p>
        </div>
        
        {system.risk_category && (
          <AIRiskBadge category={system.risk_category} size="sm" />
        )}
      </div>
      
      {/* Metadata */}
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        {system.vendor && (
          <div className="flex items-center gap-2 text-gray-400">
            <Building2 className="w-4 h-4" />
            <span>{system.vendor}</span>
          </div>
        )}
        
        {system.domain && (
          <div className="flex items-center gap-2 text-gray-400">
            <FileText className="w-4 h-4" />
            <span className="capitalize">{system.domain}</span>
          </div>
        )}
        
        {system.deployment_date && (
          <div className="flex items-center gap-2 text-gray-400">
            <Calendar className="w-4 h-4" />
            <span>{new Date(system.deployment_date).toLocaleDateString('de-DE')}</span>
          </div>
        )}
        
        {system.last_assessment_date && (
          <div className="flex items-center gap-2 text-gray-400">
            <Scan className="w-4 h-4" />
            <span>Gescannt: {new Date(system.last_assessment_date).toLocaleDateString('de-DE')}</span>
          </div>
        )}
      </div>
      
      {/* Compliance Score */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-700">
        <div className="flex items-center gap-3">
          <ComplianceProgress
            score={system.compliance_score}
            size="sm"
            showLabel={false}
          />
          <div>
            <div className="text-sm font-medium text-white">
              Compliance Score
            </div>
            <div className="text-xs text-gray-400">
              {system.compliance_score}% erfüllt
            </div>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2">
          {isNew && (
            <span className="flex items-center gap-1 text-xs text-yellow-400 bg-yellow-500/10 px-2 py-1 rounded">
              <AlertCircle className="w-3 h-3" />
              Noch nicht gescannt
            </span>
          )}
          
          <button
            onClick={() => onScan?.(system.id)}
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors"
          >
            {isNew ? 'Scan starten' : 'Neu scannen'}
          </button>
        </div>
      </div>
    </div>
  );
}
