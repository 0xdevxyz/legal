import { useEffect } from 'react';
import { useDashboardStore } from '@/stores/dashboard';
import { useLegalNews } from '@/hooks/useCompliance';

export function useDashboardInitialization() {
  const { setLegalNews, setLoading } = useDashboardStore();
  const { data: legalNews, isLoading: newsLoading } = useLegalNews();

  useEffect(() => {
    setLoading(newsLoading);
  }, [newsLoading, setLoading]);

  return {
    isLoading: newsLoading,
    legalNews
  };
}
