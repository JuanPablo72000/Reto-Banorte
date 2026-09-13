# Frontend Next.js (Banca Personal Adaptativa) — Juan Pablo.
# El puente /api/chat habla con el MCP por stdio: esta imagen incluye
# Python + el código de mcp/ para lanzar el subproceso localmente
# (ver docs/frontend/07-puente-mcp-frontend.md).
FROM node:22-slim AS base
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv/app

FROM base AS deps
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM base AS builder
COPY --from=deps /srv/app/node_modules ./node_modules
COPY frontend/ ./
COPY mcp/ ./mcp-server/
RUN npm run build

FROM base AS runtime
ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    MCP_SERVER_SCRIPT=/srv/app/mcp-server/app/server/mcp_server.py \
    BANORTE_API_BASE_URL=http://api:8000
COPY --from=builder /srv/app/.next ./.next
COPY --from=builder /srv/app/node_modules ./node_modules
COPY --from=builder /srv/app/package.json ./package.json
COPY --from=builder /srv/app/public ./public
COPY --from=builder /srv/app/mcp-server ./mcp-server
RUN python3 -m venv /opt/mcpvenv \
    && /opt/mcpvenv/bin/pip install --no-cache-dir -r ./mcp-server/requirements.txt
ENV PATH="/opt/mcpvenv/bin:${PATH}"
EXPOSE 3000
CMD ["npm", "start"]
