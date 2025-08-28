import { useCallback } from 'react';

const API_BASE = 'https://api.complyo.tech';

export interface ABTestEvent {
  event: string;
  variant: string;
  sessionId?: string;
  timestamp: string;
  [key: string]: any;
}

export const useABTestTracking = () => {
  
  const trackVariantAssignment = useCallback(async (variant: string, userType: string): Promise<string> => {
    const eventData = {
      event: 'variant_assigned',
      variant,
      user_type: userType,
      timestamp: new Date().toISOString(),
      user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
      referrer: typeof document !== 'undefined' ? document.referrer : '',
      page_location: typeof window !== 'undefined' ? window.location.href : ''
    };

    try {
      const response = await fetch(`${API_BASE}/api/analytics/ab-test`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(eventData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('✅ Variant Assignment Tracked:', result);
      return result.session_id || generateSessionId();
    } catch (error) {
      console.error('❌ Failed to track variant assignment:', error);
      return generateSessionId();
    }
  }, []);

  const trackEvent = useCallback(async (eventName: string, eventData: any = {}, sessionId?: string) => {
    const variant = typeof localStorage !== 'undefined' 
      ? localStorage.getItem('complyo_ab_variant') || 'unknown'
      : 'unknown';
    
    const payload = {
      event: eventName,
      variant,
      sessionId,
      timestamp: new Date().toISOString(),
      ...eventData
    };

    if (typeof window !== 'undefined' && typeof (window as any).gtag !== 'undefined') {
      (window as any).gtag('event', eventName, payload);
    }

    try {
      const response = await fetch(`${API_BASE}/api/analytics/event`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId || '',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      console.log(`✅ Event Tracked: ${eventName}`, payload);
    } catch (error) {
      console.error(`❌ Failed to track event ${eventName}:`, error);
    }
  }, []);

  const trackPageView = useCallback((page: string, sessionId?: string) => {
    trackEvent('page_view', { page }, sessionId);
  }, [trackEvent]);

  const trackCTAClick = useCallback((ctaName: string, position: string, sessionId?: string) => {
    trackEvent('cta_click', { 
      cta_name: ctaName, 
      position,
      timestamp: new Date().toISOString()
    }, sessionId);
  }, [trackEvent]);

  const trackEmailSignup = useCallback((email: string, plan: string, sessionId?: string) => {
    trackEvent('email_signup', { 
      plan,
      email_domain: email.split('@')[1] || 'unknown',
      timestamp: new Date().toISOString()
    }, sessionId);
  }, [trackEvent]);

  const trackCheckoutStart = useCallback((plan: string, value: number, sessionId?: string) => {
    trackEvent('begin_checkout', {
      currency: 'EUR',
      value,
      plan,
      timestamp: new Date().toISOString()
    }, sessionId);
  }, [trackEvent]);

  return {
    trackVariantAssignment,
    trackEvent,
    trackPageView,
    trackCTAClick,
    trackEmailSignup,
    trackCheckoutStart
  };
};

function generateSessionId(): string {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2);
  return `${timestamp}_${randomPart}`;
}
