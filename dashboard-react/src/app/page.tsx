export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'
export const runtime = 'nodejs'

import { WebsiteAnalysis } from '@/components/dashboard/WebsiteAnalysis'
import { MetricsCards } from '@/components/dashboard/MetricsCards'
import { LegalNews } from '@/components/dashboard/LegalNews'

export default function Page() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <MetricsCards />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <WebsiteAnalysis />
          <LegalNews />
        </div>
      </div>
    </div>
  )
}
