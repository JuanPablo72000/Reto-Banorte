# Servidor MCP (BancaAdaptativa) — Guillermo.
# Transporte por defecto: stdio (lo usa el puente Next.js en dev, igual que
# mcp_client.py). En docker-compose el servicio `mcp` expone el puerto 8080:
# con MCP_TRANSPORT=http el servidor levanta streamable-http en ese puerto
# (opción documentada como futura en docs/frontend/07-puente-mcp-frontend.md).
FROM python:3.12-slim
WORKDIR /srv/mcp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY mcp_client.py test_local.py ./

ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8080 \
    BANORTE_API_BASE_URL=http://api:8000

EXPOSE 8080

CMD ["sh", "-c", "if [ \"$MCP_TRANSPORT\" = \"http\" ]; then python -m app.server.mcp_server --http; else python -m app.server.mcp_server; fi"]
