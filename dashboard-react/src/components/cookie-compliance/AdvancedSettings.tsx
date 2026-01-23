/**
 * Advanced Settings - All Cookie Compliance Features
 */

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings, Globe, Shield, Users, FileText, Eye, 
  Share2, ToggleRight, Zap 
} from 'lucide-react';

// Import all feature components
import ConsentModeSettings from './ConsentModeSettings';
import AgeVerification from './AgeVerification';
import GeoRestriction from './GeoRestriction';
import TCFManager from './TCFManager';
import CookiePolicyGenerator from './CookiePolicyGenerator';
import AccessibilityScore from './AccessibilityScore';

interface AdvancedSettingsProps {
  siteId: string;
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

export default function AdvancedSettings({ siteId, config, onSave }: AdvancedSettingsProps) {
  const [activeTab, setActiveTab] = useState('consent-mode');

  const features = [
    { 
      id: 'consent-mode', 
      label: 'Consent Mode', 
      icon: Zap,
      badge: 'Pflicht',
      badgeColor: 'bg-red-500'
    },
    { 
      id: 'age-verification', 
      label: 'Jugendschutz', 
      icon: Users,
      badge: null
    },
    { 
      id: 'geo-restriction', 
      label: 'Geo', 
      icon: Globe,
      badge: null
    },
    { 
      id: 'tcf', 
      label: 'TCF 2.2', 
      icon: Shield,
      badge: 'Beta',
      badgeColor: 'bg-yellow-500'
    },
    { 
      id: 'policy', 
      label: 'Richtlinie', 
      icon: FileText,
      badge: null
    },
    { 
      id: 'accessibility', 
      label: 'A11y', 
      icon: Eye,
      badge: null
    },
  ];

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6 bg-gray-900/50 p-1 h-auto">
          {features.map(feature => (
            <TabsTrigger 
              key={feature.id}
              value={feature.id}
              className="relative gap-1.5 data-[state=active]:bg-orange-500 data-[state=active]:text-white transition-all py-2.5 px-2 text-xs"
            >
              <feature.icon className="w-4 h-4" />
              <span className="hidden lg:inline">{feature.label}</span>
              {feature.badge && (
                <span className={`absolute -top-1 -right-1 px-1 py-0.5 text-[10px] rounded ${feature.badgeColor} text-white`}>
                  {feature.badge}
                </span>
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="consent-mode" className="mt-6">
          <ConsentModeSettings siteId={siteId} config={config} onSave={onSave} />
        </TabsContent>

        <TabsContent value="age-verification" className="mt-6">
          <AgeVerification siteId={siteId} config={config} onSave={onSave} />
        </TabsContent>

        <TabsContent value="geo-restriction" className="mt-6">
          <GeoRestriction siteId={siteId} config={config} onSave={onSave} />
        </TabsContent>

        <TabsContent value="tcf" className="mt-6">
          <TCFManager siteId={siteId} config={config} onSave={onSave} />
        </TabsContent>

        <TabsContent value="policy" className="mt-6">
          <CookiePolicyGenerator siteId={siteId} config={config} />
        </TabsContent>

        <TabsContent value="accessibility" className="mt-6">
          <AccessibilityScore config={config} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
