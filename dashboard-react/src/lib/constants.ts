export const APP_CONFIG = {
  name: 'Complyo Dashboard',
  version: '2.0.0',
  description: 'KI-gestützte Website-Compliance für Deutschland',
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech',
    timeout: 30000
  },
  dashboard: {
    refreshInterval: 30000, // 30 seconds
    chartPoints: 120, // 120 days trend
    autoRefresh: true
  }
} as const;

export const COMPLIANCE_THRESHOLDS = {
  excellent: 90,
  good: 75,
  warning: 50,
  critical: 30
} as const;

export const RISK_CATEGORIES = {
  critical: {
    color: 'red',
    icon: 'AlertTriangle',
    label: 'Kritisch'
  },
  medium: {
    color: 'yellow', 
    icon: 'AlertCircle',
    label: 'Warnung'
  },
  low: {
    color: 'green',
    icon: 'CheckCircle',
    label: 'OK'
  }
} as const;
