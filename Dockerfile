# PayStream — Multi-runtime Docker image for Cloud Run
# Runs: Node.js (WDK MCP server) + Python (LangGraph agent) + React dashboard (static)

# ── Stage 1: Build React dashboard ──────────────────────────────────
FROM node:20-slim AS dashboard-build
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm install
COPY dashboard/ .
RUN npm run build

# ── Stage 2: Install WDK server dependencies ────────────────────────
FROM node:20-slim AS wdk-deps
WORKDIR /app/wdk-server
COPY wdk-server/package.json wdk-server/package-lock.json* ./
RUN npm install --production

# ── Stage 3: Final runtime (Python + Node.js) ───────────────────────
FROM python:3.11-slim

# Install Node.js 20 in the Python image
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy WDK server + node_modules
COPY wdk-server/ ./wdk-server/
COPY --from=wdk-deps /app/wdk-server/node_modules ./wdk-server/node_modules

# Copy Python agent
COPY agent/ ./agent/

# Copy built dashboard static files
COPY --from=dashboard-build /app/dashboard/dist ./dashboard/dist

# Install Python dependencies
RUN pip install --no-cache-dir -r agent/requirements.txt

# Cloud Run provides PORT env var (default 8080)
ENV PORT=8080

EXPOSE 8080

# Start the FastAPI agent server
CMD ["python", "agent/server.py"]
