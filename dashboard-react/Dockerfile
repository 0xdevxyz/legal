# ===========================
# Stage 1: Dependencies
# ===========================
FROM node:18-alpine AS deps
WORKDIR /app

# Copy package files
COPY package*.json package-lock*.json* ./

# Install dependencies
RUN npm ci --only=production

# ===========================
# Stage 2: Builder
# ===========================
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm install

# Copy source code
COPY . .

# Set build-time environment variables
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=https://api.complyo.tech
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# ===========================
# Stage 3: Runner (Production)
# ===========================
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_PUBLIC_API_URL https://api.complyo.tech

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set correct permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT 3000

# Start Next.js in standalone mode
CMD ["node", "server.js"]
