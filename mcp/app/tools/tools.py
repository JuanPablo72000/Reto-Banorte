"""
Implementaciones de las tools de datos - parte de Guillermo (MCP + IA),
reconectadas por Cain a la API real (integration/api_client.py).

Separadas de server/mcp_server.py a proposito: aqui solo hay funciones
Python normales (faciles de probar/testear sueltas, sin levantar FastMCP);
el servidor (server/mcp_server.py) se limita a registrarlas con
`@mcp.tool()`.

Las firmas de las 8 tools NO cambiaron respecto a la version con mocks
(placeholders/mock_data.py) - eso permite que el resto del contrato A2UI
siga funcionando igual.

Nota sobre autenticacion: por ahora se usa UN SOLO cliente autenticado a
nivel de proceso, con el unico usuario sembrado hoy en Data/DbSeeder.cs
(demo@banorte.mx). No hay manejo por-usuario todavia - eso es una
decision de equipo pendiente, fuera del alcance de este archivo. El
parametro id_user se sigue recibiendo (no se toco la firma) pero por
ahora solo se usa para logging, no para autenticar.

search_memory_context sigue en mock a proposito: Pablo todavia no expone
/memory/query en BancaAdaptativa.Api.
"""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Optional

from app.placeholders import mock_data
from app.ia.groq_client import GroqPlanner
from app.integration.api_client import BancaApiClient
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

# --- Cliente HTTP hacia BancaAdaptativa.Api ---------------------------------
# Un solo cliente por proceso, logueado una vez con el usuario demo del seed.
# TODO (equipo): si mas adelante hay login real / multiples usuarios, esto
# se reemplaza por un mecanismo por-usuario - no forma parte de este cambio.
_client: Optional[BancaApiClient] = None


async def _get_client() -> BancaApiClient:
    global _client
    if _client is None:
        _client = BancaApiClient()
        email = os.getenv("BANORTE_DEMO_EMAIL", "demo@banorte.mx")
        password = os.getenv("BANORTE_DEMO_PASSWORD", "Demo123!")
        await _client.login(email, password)
    return _client


async def get_user_context(id_user: int) -> UserContext:
    """Devuelve el perfil del usuario y sus preferencias de accesibilidad.
    Equivale a GET /users/me + GET /me/preferences."""
    logger.info("Tool 'get_user_context' invocada (id_user=%s)", id_user)
    client = await _get_client()
    user_raw = await client.get_user_me()
    prefs_raw = await client.get_me_preferences()
    return UserContext.model_validate({**user_raw, "accessibility": prefs_raw})


async def get_accounts(id_user: int) -> list[Account]:
    """Devuelve las cuentas del usuario. Equivale a GET /accounts."""
    logger.info("Tool 'get_accounts' invocada (id_user=%s)", id_user)
    client = await _get_client()
    raw_accounts = await client.get_accounts()
    return [Account.model_validate(item) for item in raw_accounts]


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
    client = await _get_client()
    raw_transactions = await client.get_account_transactions(
        id_account, date_from=date_from, date_to=date_to, limit=limit
    )
    return [Transaction.model_validate(item) for item in raw_transactions]


async def get_daily_balance(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[DailyBalance]:
    """Devuelve el balance diario de una cuenta. Equivale a
    GET /accounts/{accountId}/daily-balances."""
    logger.info("Tool 'get_daily_balance' invocada (id_account=%s)", id_account)
    client = await _get_client()
    raw_balances = await client.get_account_daily_balances(
        id_account, date_from=date_from, date_to=date_to
    )
    return [DailyBalance.model_validate(item) for item in raw_balances]


async def search_memory_context(
    id_user: int,
    query: str,
    id_session: Optional[int] = None,
    limit: int = 10,
) -> list[dict]:
    """Busca contexto de sesion ya redactado y permitido (memoria de la IA,
    nunca datos sensibles completos). Equivale a POST /memory/query
    (aun no existe en la API real: ver MemoryEvent en schemas.py).
    SIGUE EN MOCK A PROPOSITO - Pablo todavia no expone este endpoint."""
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
    """Crea un BORRADOR de transferencia (aun no confirmado). Equivale a
    POST /transfers. Requiere confirmacion posterior con confirm_transfer.

    Nota: esta tool no recibe destination_masked (su firma no cambio). El
    OpenAPI real marca ese campo como nullable, asi que se manda vacio -
    ajustar si el equipo decide derivarlo de otra forma."""
    logger.info(
        "Tool 'prepare_transfer' invocada (id_user=%s, id_origin_account=%s, alias=%s, amount=%.2f)",
        id_user, id_origin_account, destination_alias, amount,
    )
    if amount <= 0:
        raise ValueError("El monto de la transferencia debe ser mayor a 0")
    client = await _get_client()
    raw_transfer = await client.create_transfer(
        id_origin_account=id_origin_account,
        destination_alias=destination_alias,
        destination_masked="",
        amount=amount,
        currency=currency,
        concept=concept,
    )
    return Transfer.model_validate(raw_transfer)


async def confirm_transfer(id_transfer: int, method: str = "app") -> Transfer:
    """Confirma una transferencia previamente creada con prepare_transfer.
    Equivale a POST /transfers/{transferId}/confirm."""
    logger.info("Tool 'confirm_transfer' invocada (id_transfer=%s, method=%s)", id_transfer, method)
    client = await _get_client()
    raw_result = await client.confirm_transfer(id_transfer, method)
    # El client regresa {"transfer": ..., "confirmation": ...}, no un Transfer plano.
    return Transfer.model_validate(raw_result["transfer"])


async def get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliacion entre transferencias y
    movimientos. Equivale a GET /reconciliation.

    Nota: el endpoint real no acepta filtros por query param (ver
    OpenAPI), asi que se trae la lista completa y se filtra aqui - igual
    que hacia el mock. id_user e id_account no existen en
    ReconciliationMatch, se ignoran igual que en el mock."""
    logger.info(
        "Tool 'get_reconciliation_status' invocada (id_user=%s, id_transfer=%s, id_account=%s)",
        id_user, id_transfer, id_account,
    )
    client = await _get_client()
    raw_items = await client.get_reconciliation()
    items = [ReconciliationMatch.model_validate(item) for item in raw_items]
    if id_transfer is not None:
        items = [r for r in items if r.id_transfer == id_transfer]
    return items


async def planificar_accion(mensaje_usuario: str, contexto: Optional[dict] = None) -> ActionPlan:
    """
    Genera un plan de accion tipado (ActionPlan) a partir de la intencion
    del usuario, indicando que tools de las 8 de arriba conviene invocar,
    con que argumentos (IDs enteros reales o null) y con que "ui_hint"
    deberia mostrarse cada paso en la interfaz.

    Args:
        mensaje_usuario: lo que el usuario quiere hacer, en lenguaje natural
            (ej. "quiero ver mis movimientos del mes" o "transfiere $500 a mi hermano").
        contexto: datos ya conocidos de la sesion (ej. {"id_user": 1, "id_account": 1}),
            para que el modelo no tenga que adivinar los IDs.

    Returns:
        ActionPlan (ver schemas.py): intent, steps (cada uno con tool,
        ui_hint, arguments tipados y reason), needs_confirmation,
        response_to_user.
    """
    logger.info("Tool 'planificar_accion' invocada")
    return await _planner.plan(user_message=mensaje_usuario, context=contexto)