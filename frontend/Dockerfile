# Install workspace dependencies
FROM oven/bun:1 AS deps
WORKDIR /app
COPY package.json bun.lock ./
COPY frontend/package.json ./frontend/
RUN bun install --frozen-lockfile

# Build the Next.js app into a standalone server
FROM oven/bun:1 AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY package.json bun.lock ./
COPY frontend ./frontend
WORKDIR /app/frontend
RUN bun run build

# Minimal runtime image running the standalone output
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
COPY --from=builder /app/frontend/.next/standalone ./
COPY --from=builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=builder /app/frontend/public ./frontend/public
EXPOSE 3000
CMD ["node", "frontend/server.js"]
