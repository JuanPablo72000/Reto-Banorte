# MCP + IA — Guillermo

Servidor MCP y planificador de IA (Groq) del proyecto **Banca Personal
Adaptativa**, ya migrado para trabajar con IDs enteros reales de
`backend/src/BancaAdaptativa.Api` (Pablo) en vez de los placeholders de
texto de la versión anterior (previa a que existiera el backend real).

## Estructura

```
mcp/
├── app/
│   ├── schemas/schemas.py     # Modelos Pydantic == DTOs reales (IdUser, IdAccount...)
│   ├── ia/
│   │   ├── groq_client.py     # GroqPlanner: genera el ActionPlan (IDs int o null)
│   │   ├── plan_normalizer.py # Corrige typos/placeholders inválidos antes de validar
│   │   └── contract_catalog.py# Carga y valida contra contracts/a2ui/a2ui-mcp-contract.yaml
│   ├── integration/api_client.py # Cliente HTTP real (Cain) contra BancaAdaptativa.Api
│   ├── placeholders/mock_data.py # Mocks alineados 1:1 al seed de Pablo (DbSeeder.cs)
│   ├── tools/tools.py         # Las 8 tools de datos + planificar_accion (funciones puras)
│   ├── server/mcp_server.py   # Registra las tools con FastMCP (@mcp.tool)
│   └── logging_config.py      # Logging a stderr (obligatorio: stdio usa stdout)
├── mcp_client.py               # Cliente de prueba end-to-end vía protocolo MCP
├── test_local.py               # Prueba GroqPlanner directo, sin MCP
├── requirements.txt
└── .env.example
```

## Usuario/cuenta semilla (para pruebas)

Igual que `backend/src/BancaAdaptativa.Api/Data/DbSeeder.cs`:

- `id_user = 1` — demo@banorte.mx — perfil con discapacidad visual
- `id_account = 1` — cuenta "Nómina" ****1234 — saldo 25,400.50 MXN
- `id_transfer = 1` — $2,000 MXN a "Mamá" (****5678), status `pending`

## Cómo correr

```bash
cd mcp
python -m venv venv && source venv/bin/activate   # o venv\Scripts\activate en Windows
pip install -r requirements.txt
cp .env.example .env   # y pon tu GROQ_API_KEY real

# Prueba solo el planificador de IA (sin protocolo MCP):
python test_local.py

# Prueba el servidor completo vía protocolo MCP real:
python mcp_client.py "Quiero ver mis movimientos del mes pasado"

# Levantar el servidor MCP solo (modo stdio, para un host MCP real):
python -m app.server.mcp_server
```

## Qué falta para que Cain conecte la API real

Cada función `mock_*` de `mcp/app/placeholders/mock_data.py` documenta, en su
docstring, exactamente qué método de `mcp/app/integration/api_client.py`
(`BancaApiClient`) la reemplaza. El cambio es SOLO en el cuerpo de
`mcp/app/tools/tools.py` (llamar a `BancaApiClient` en vez de `mock_data`) —
las firmas de las 8 tools y de `planificar_accion` no cambian, así que el
frontend y el resto del contrato A2UI siguen funcionando igual.

Las dos excepciones son `search_memory_context` y todo lo relacionado con
`MemoryEvent`/`AuditLog`: Pablo aún no expone `/memory/query` ni
`/audit/me` en `Endpoints/*.cs`, así que esas siguen siendo mock incluso
después de conectar todo lo demás.
