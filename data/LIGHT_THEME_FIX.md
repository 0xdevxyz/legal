# Light Theme Force Fix

## Changes Made

### /home/clawd/saas/legal/landing-react/src/app/layout.tsx
1. Line 46: `<html lang="de" className="scroll-smooth">` -> `<html lang="de" className="scroll-smooth light">`
2. Line 48: Removed entire `<script dangerouslySetInnerHTML=...>` dark mode detection script

### Components checked (no dark backgrounds found, no changes needed)
- AnalyticsSection.tsx - clean (light backgrounds only)
- PricingSection.tsx - clean (light backgrounds only)
- IntegrationsSection.tsx - clean (light backgrounds only)
- TestimonialsSection.tsx - clean (light backgrounds only)
