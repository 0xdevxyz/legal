'use client';

import { useQuery } from '@tanstack/react-query';
import { getMyAddons } from '@/lib/ai-compliance-api';

/**
 * Single source of truth for ComploAI-Guard access.
 *
 * AI-Compliance is sold as the monthly add-on `comploai_guard` (not a plan tier).
 * Every place that gates the AI-Compliance feature — nav links, dashboard card,
 * the /ai-compliance route guard — derives its answer from this hook so the
 * behaviour can never drift apart again.
 */
export function useComploaiGuard() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-addons'],
    queryFn: getMyAddons,
    staleTime: 60_000,
    retry: false,
  });

  const hasComploaiGuard = !!data?.addons?.some(
    (a) => a.addon_key === 'comploai_guard' && a.status === 'active'
  );

  return { hasComploaiGuard, isLoading };
}
