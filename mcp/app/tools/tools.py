"""
Implementaciones de las tools de datos — parte de Guillermo (MCP + IA).

Separadas de server/mcp_server.py a propósito: aquí solo hay funciones
Python normales (fáciles de probar/testear sueltas, sin levantar FastMCP);
el servidor (server/mcp_server.py) se limita a registrarlas con
`@mcp.tool()`.

Todas usan los IDs enteros reales (IdUser, IdAccount, IdTransfer...) de
BancaAdaptativa.Api y, por ahora, están respaldadas por
placeholders/mock_data.py (que refleja 1:1 el seed de Pablo en
Data/DbSeeder.cs). Cain las reconecta a integration/api_client.py cuando
la integración esté lista, sin tocar estas firmas.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from app.placeholders import mock_data
from app.ia.groq_client import GroqPlanner
from app.schemas import (
    Account,
    ActionPlan,
    DailyBalance,
    ReconciliationMatch,
    Transaction,
    Transfer,
    UserContext,
)

logger = logging.getLogger("mcp_ia.tools")

# Un solo GroqPlanner por proceso: reutiliza el cliente AsyncGroq entre llamadas.
_planner = GroqPlanner()


async def get_user_context(id_user: int) -> UserContext:
    """Devuelve el perfil del usuario y sus preferencias de accesibilidad.
    Equivale a GET /users/me + GET /me/preferences."""
    logger.info("Tool 'get_user_context' invocada (id_user=%s)", id_user)
    context = mock_data.mock_get_user_context(id_user)
    if context is None:
        raise ValueError(f"Usuario no encontrado: id_user={id_user}")
    return context


async def get_accounts(id_user: int) -> list[Account]:
    """Devuelve las cuentas del usuario. Equivale a GET /accounts."""
    logger.info("Tool 'get_accounts' invocada (id_user=%s)", id_user)
    client = await get_client_for_user(id_user)  # lo que ya tengan resuelto
    raw_accounts = await client.get_accounts()
    return [Account.model_validate(item) for item in raw_accounts]
    #return mock_data.mock_get_accounts(id_user)


async def get_transactions(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 20,
) -> list[Transaction]:
    """Devuelve los movimientos de una cuenta, opcionalmente filtrados por
    rango de fecha. Equivale a GET /accounts/{accountId}/transactions."""
    logger.info(
        "Tool 'get_transactions' invocada (id_account=%s, date_from=%s, date_to=%s, limit=%d)",
        id_account, date_from, date_to, limit,
    )
    return mock_data.mock_get_transactions(id_account, date_from, date_to, limit)


async def get_daily_balance(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[DailyBalance]:
    """Devuelve el balance diario de una cuenta. Equivale a
    GET /accounts/{accountId}/daily-balances."""
    logger.info("Tool 'get_daily_balance' invocada (id_account=%s)", id_account)
    return mock_data.mock_get_daily_balance(id_account, date_from, date_to)


async def search_memory_context(
    id_user: int,
    query: str,
    id_session: Optional[int] = None,
    limit: int = 10,
) -> list[dict]:
    """Busca contexto de sesión ya redactado y permitido (memoria de la IA,
    nunca datos sensibles completos). Equivale a POST /memory/query
    (aún no existe en la API real: ver MemoryEvent en schemas.py)."""
    logger.info("Tool 'search_memory_context' invocada (id_user=%s, query=%r)", id_user, query)
    return mock_data.mock_search_memory_context(id_user, query, id_session, limit)


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
    logger.info(
        "Tool 'prepare_transfer' invocada (id_user=%s, id_origin_account=%s, alias=%s, amount=%.2f)",
        id_user, id_origin_account, destination_alias, amount,
    )
    if amount <= 0:
        raise ValueError("El monto de la transferencia debe ser mayor a 0")
    return mock_data.mock_prepare_transfer(
        id_user, id_origin_account, destination_alias, amount, currency, concept
    )


async def confirm_transfer(id_transfer: int, method: str = "app") -> Transfer:
    """Confirma una transferencia previamente creada con prepare_transfer.
    Equivale a POST /transfers/{transferId}/confirm."""
    logger.info("Tool 'confirm_transfer' invocada (id_transfer=%s, method=%s)", id_transfer, method)
    transfer = mock_data.mock_confirm_transfer(id_transfer, method)
    if transfer is None:
        raise ValueError(f"Transferencia no encontrada: id_transfer={id_transfer}")
    return transfer


async def get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliación entre transferencias y
    movimientos. Equivale a GET /reconciliation."""
    logger.info(
        "Tool 'get_reconciliation_status' invocada (id_user=%s, id_transfer=%s, id_account=%s)",
        id_user, id_transfer, id_account,
    )
    return mock_data.mock_get_reconciliation_status(id_user, id_transfer, id_account)


async def planificar_accion(mensaje_usuario: str, contexto: Optional[dict] = None) -> ActionPlan:
    """
    Genera un plan de acción tipado (ActionPlan) a partir de la intención
    del usuario, indicando qué tools de las 8 de arriba conviene invocar,
    con qué argumentos (IDs enteros reales o null) y con qué "ui_hint"
    debería mostrarse cada paso en la interfaz.

    Args:
        mensaje_usuario: lo que el usuario quiere hacer, en lenguaje natural
            (ej. "quiero ver mis movimientos del mes" o "transfiere $500 a mi hermano").
        contexto: datos ya conocidos de la sesión (ej. {"id_user": 1, "id_account": 1}),
            para que el modelo no tenga que adivinar los IDs.

    Returns:
        ActionPlan (ver schemas.py): intent, steps (cada uno con tool,
        ui_hint, arguments tipados y reason), needs_confirmation,
        response_to_user. Cain reemplaza la ejecución de "steps" por
        llamadas reales a la API cuando esté lista; el front puede
        recorrer "steps" para dibujar la UI usando "ui_hint".
    """
    logger.info("Tool 'planificar_accion' invocada")
    return await _planner.plan(user_message=mensaje_usuario, context=contexto)
