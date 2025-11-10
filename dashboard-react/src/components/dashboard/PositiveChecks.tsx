'use client'

import { CheckCircle } from 'lucide-react'

interface PositiveCheck {
  category: string
  title: string
  status: string
  icon: string
}

interface PositiveChecksProps {
  checks: PositiveCheck[]
}

export function PositiveChecks({ checks }: PositiveChecksProps) {
  if (!checks || checks.length === 0) {
    return null
  }

  return (
    <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-lg p-6 border border-green-500/30">
      <div className="flex items-center gap-3 mb-4">
        <CheckCircle className="w-6 h-6 text-green-400" />
        <h3 className="text-xl font-bold text-green-400">
          ✅ Was bereits funktioniert
        </h3>
      </div>
      
      <p className="text-gray-300 text-sm mb-4">
        Diese Compliance-Anforderungen erfüllt Ihre Website bereits:
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {checks.map((check, index) => (
          <div
            key={index}
            className="flex items-center gap-3 p-3 bg-green-500/5 rounded-lg border border-green-500/20 hover:border-green-500/40 transition-all"
          >
            <div className="flex-shrink-0">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200 font-medium">
                {check.title}
              </p>
              <p className="text-xs text-gray-400 capitalize">
                {check.category}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <p className="text-xs text-blue-300">
          💡 <strong>Tipp:</strong> Behalten Sie diese Punkte im Blick, um Ihre Compliance dauerhaft zu sichern.
        </p>
      </div>
    </div>
  )
}

