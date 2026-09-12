"""
Servidor MCP — parte de Guillermo (MCP + modelo de IA).

Qué expone este servidor (sección 5 del resumen — "Tools ejemplo"):
  1. Las 8 tools de datos acordadas con el equipo, cada una con entrada y
     salida tipadas (Pydantic, en schemas/schemas.py) y respaldadas por
     mocks (placeholders/mock_data.py, alineados 1:1 al seed real de Pablo)
     hasta que Cain conecte integration/api_client.py:
       - get_user_context
       - get_accounts
       - get_transactions
       - get_daily_balance
       - search_memory_context
       - prepare_transfer
       - confirm_transfer
       - get_reconciliation_status
  2. Una tool adicional de orquestación con IA, `planificar_accion`, que le
     pide a Groq un ActionPlan (schemas.py) indicando qué tools de las 8
     conviene invocar para cumplir la intención del usuario, con qué
     argumentos (IDs enteros reales o null) y con qué "ui_hint" debería
     mostrarse cada paso en la interfaz.

Las implementaciones viven en tools/tools.py (funciones planas, fáciles de
probar sin levantar FastMCP); aquí solo se registran con `@mcp.tool()`.

Uso (desde la carpeta mcp/, con el venv activo):
    python -m app.server.mcp_server
"""

import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# Este archivo se lanza como script (`python app/server/mcp_server.py`, ya
# sea directo o vía fastmcp.Client desde mcp_client.py). Python solo agrega
# al sys.path la carpeta del propio script (app/server/), no la raíz del
# paquete `app` (mcp/), así que sin esto "from app import ..." fallaría con
# ModuleNotFoundError salvo que ya se ejecute con `python -m app.server.mcp_server`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

# Debe cargarse ANTES de importar app.ia.groq_client (vía tools.py), porque
# ese módulo lee GROQ_API_KEY con os.getenv() apenas se importa.
load_dotenv()

from fastmcp import FastMCP

from app import tools
from app.logging_config import setup_logging
from app.schemas import (
    Account,
    ActionPlan,
    DailyBalance,
    ReconciliationMatch,
    Transaction,
    Transfer,
    UserContext,
)

# 1. Logging seguro a stderr (nunca a stdout, por el transporte stdio de MCP)
logger = setup_logging(level=logging.INFO)

# 2. Instancia del servidor MCP
mcp = FastMCP("MCP_Banca_IA")


# ---------------------------------------------------------------------------
# TOOLS DE DATOS (respaldadas por placeholders/mock_data.py por ahora,
# mismas firmas/tipos que tendrá la integración real de Cain)
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_user_context(id_user: int) -> UserContext:
    """Devuelve el perfil del usuario y sus preferencias de accesibilidad.
    Equivale a GET /users/me + GET /me/preferences."""
    return await tools.get_user_context(id_user)


@mcp.tool()
async def get_accounts(id_user: int) -> list[Account]:
    """Devuelve las cuentas del usuario. Equivale a GET /accounts."""
    return await tools.get_accounts(id_user)


@mcp.tool()
async def get_transactions(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 20,
) -> list[Transaction]:
    """Devuelve los movimientos de una cuenta, opcionalmente filtrados por
    rango de fecha. Equivale a GET /accounts/{accountId}/transactions."""
    return await tools.get_transactions(id_account, date_from, date_to, limit)


@mcp.tool()
async def get_daily_balance(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[DailyBalance]:
    """Devuelve el balance diario de una cuenta. Equivale a
    GET /accounts/{accountId}/daily-balances."""
    return await tools.get_daily_balance(id_account, date_from, date_to)


@mcp.tool()
async def search_memory_context(
    id_user: int,
    query: str,
    id_session: Optional[int] = None,
    limit: int = 10,
) -> list[dict]:
    """Busca contexto de sesión ya redactado y permitido (memoria de la IA,
    nunca datos sensibles completos). Equivale a POST /memory/query."""
    return await tools.search_memory_context(id_user, query, id_session, limit)


@mcp.tool()
async def prepare_transfer(
    id_user: int,
    id_origin_account: int,
    destination_alias: str,
    amount: float,
    currency: str = "MXN",
    concept: str = "",
) -> Transfer:
    """Crea un BORRADOR de transferencia (aún no confirmado). Equivale a
    POST /transfers. Requiere confirmación posterior con confirm_transfer."""
    return await tools.prepare_transfer(id_user, id_origin_account, destination_alias, amount, currency, concept)


@mcp.tool()
async def confirm_transfer(id_transfer: int, method: str = "app") -> Transfer:
    """Confirma una transferencia previamente creada con prepare_transfer.
    Equivale a POST /transfers/{transferId}/confirm."""
    return await tools.confirm_transfer(id_transfer, method)


@mcp.tool()
async def get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliación entre transferencias y
    movimientos. Equivale a GET /reconciliation."""
    return await tools.get_reconciliation_status(id_user, id_transfer, id_account)


# ---------------------------------------------------------------------------
# TOOL DE ORQUESTACIÓN CON IA
# ---------------------------------------------------------------------------
@mcp.tool()
async def planificar_accion(mensaje_usuario: str, contexto: Optional[dict] = None) -> ActionPlan:
    """
    Genera un plan de acción tipado (ActionPlan) a partir de la intención
    del usuario, indicando qué tools de las 8 de arriba conviene invocar,
    con qué argumentos (IDs enteros reales o null) y con qué "ui_hint"
    (form, table, confirmation, summary, none) debería mostrarse cada paso
    en la interfaz.

    Args:
        mensaje_usuario: lo que el usuario quiere hacer, en lenguaje natural.
        contexto: datos ya conocidos de la sesión, ej. {"id_user": 1, "id_account": 1},
            para que el modelo no tenga que adivinar los IDs.
    """
    return await tools.planificar_accion(mensaje_usuario, contexto)


if __name__ == "__main__":
    logger.info("Arrancando servidor MCP en modo stdio")
    mcp.run(transport="stdio")
