'use client';

/**
 * DEPRECATED – Dieser Komponente wurde durch den Cookie-Compliance-Wizard ersetzt.
 * Leitet Nutzer automatisch zur vollständigen Cookie-Compliance-Seite weiter.
 * @deprecated Seit 2026-05 – verwende /cookie-compliance
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { Cookie, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export const CookieBannerManagement: React.FC = () => {
  const router = useRouter();

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cookie className="w-6 h-6 text-orange-400" />
          Cookie-Banner Management
        </CardTitle>
        <p className="text-sm text-gray-400 mt-2">
          Verwalten Sie Ihren Cookie-Banner direkt über Complyo – DSGVO & TTDSG konform
        </p>
      </CardHeader>

      <CardContent>
        <div className="flex flex-col items-center justify-center py-8 text-center gap-4">
          <Cookie className="w-16 h-16 text-orange-400/50" />
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">
              Cookie-Compliance Wizard
            </h3>
            <p className="text-sm text-gray-400 max-w-md">
              Nutzen Sie den neuen Cookie-Compliance-Wizard zum Scannen Ihrer Website,
              Konfigurieren des Banners und Einbinden des Codes – alles in einem Schritt.
            </p>
          </div>
          <Button
            onClick={() => router.push('/cookie-compliance')}
            className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 gap-2"
          >
            Zum Cookie-Compliance Wizard
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
