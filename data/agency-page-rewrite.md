# Agency Page Rewrite Plan

## Key findings:
- SidebarLayout uses inline flex styles, not Tailwind wrapper
- cookie-compliance/page.tsx uses `<main>` with `min-h-screen bg-gray-900 text-white` (no SidebarLayout — it's a sub-page)
- AuthContext user.plan_type can be 'agency' | 'free' | 'single' | 'pro' | 'expert' | 'update'
- apiClient from @/lib/api uses axios with auto-token injection
- API endpoint: /api/cookie-compliance/agency/stats returns AgencyStats

## Plan:
- Wrap in SidebarLayout (like other dashboard pages)
- SiteStat gets `url` field added alongside site_id
- Loading: skeleton cards + skeleton table rows
- Error: centered error card with retry button
- No agency plan: upgrade banner (paywall guard)
- Stats grid: 4 cards (total_sites, total_impressions, overall_acceptance_rate, active_clients)
- Client table: site_id/url, impressions, acceptance_rate, status badge
- Empty state: icon + text when sites.length === 0
- Dark mode: bg-zinc-950 page, bg-zinc-900 cards, border-zinc-800
