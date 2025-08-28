# Complyo Dashboard Structure

```
src/
├── app/                    # Next.js App Router
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   ├── page.tsx           # Dashboard home
│   ├── login/             # Authentication
│   └── api/               # API routes
├── components/            # React components
│   ├── ui/               # Base UI components
│   ├── dashboard/        # Dashboard-specific
│   └── charts/           # Chart components
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   ├── utils.ts         # Helper functions
│   └── constants.ts     # App constants
├── types/               # TypeScript types
│   ├── dashboard.ts     # Dashboard types
│   └── api.ts          # API response types
├── hooks/              # Custom React hooks
│   ├── useCompliance.ts # Compliance data
│   └── useAuth.ts      # Authentication
└── stores/             # State management
    ├── dashboard.ts    # Dashboard state
    └── auth.ts        # Auth state
```
