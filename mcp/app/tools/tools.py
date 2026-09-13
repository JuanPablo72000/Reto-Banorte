"""
Implementaciones de las tools de datos — parte de Guillermo (MCP + IA).

Separadas de server/mcp_server.py a propósito: aquí solo hay funciones
Python normales (fáciles de probar/testear sueltas, sin levantar FastMCP);
el servidor (server/mcp_server.py) se limita a registrarlas con
`@mcp.tool()`.

CONEXIÓN A LA API REAL (Cain): cada tool intenta primero
BancaAdaptativa.Api vía integration/api_client.py (con login automático
del usuario semilla, ver integration/connection.py) y, si la API falla
por lo que sea (apagada, 4xx/5xx, validación), usa como respaldo
placeholders/mock_data.py (que refleja 1:1 el seed de Pablo en
Data/DbSeeder.cs). Las respuestas reales vienen con
`x_placeholder=False`; las de mock, con `x_placeholder=True`.

Modo con BANORTE_API_MODE (ver mcp/.env.example):
- "auto"  (default): API real con fallback a mock.
- "api":   solo API real; si falla, se propaga el error.
- "mock":  solo mocks (comportamiento anterior a la integración).

Todas usan los IDs enteros reales (IdUser, IdAccount, IdTransfer...) de
BancaAdaptativa.Api y cubren los endpoints NUEVOS de Pablo
(account-summary, account detail, /me/transactions, /transfers
listado+detalle, statements, expense-categories, budgets monthly,
savings-goals y credit-cards). Todas de SOLO LECTURA salvo
prepare_transfer/confirm_transfer — ver docs/datos/06-catalogo-ia-
placeholders.md sección 6.5: la IA no crea presupuestos, tarjetas ni
metas, eso lo hace el usuario desde la UI.

Excepción: search_memory_context sigue siendo 100% mock (no existe
/memory/query en Endpoints/*.cs todavía) y planificar_accion usa
PlannerIA (no toca la API de banca).
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from typing import Awaitable, Callable, Optional, TypeVar

from app.placeholders import mock_data
from app.ia.ia_client import PlannerIA
from app.integration.connection import api_mode, call_api
from app.schemas import (
    AccessibilityPreference,
    AccessibilityProfile,
    Account,
    AccountSummary,
    ActionPlan,
    BudgetMonthlySummary,
    CreditCard,
    CreditCardStatement,
    DailyBalance,
    ExpenseCategory,
    ReconciliationMatch,
    SavingsGoal,
    Statement,
    StatementDetail,
    Transaction,
    Transfer,
    UserContext,
)

logger = logging.getLogger("mcp_ia.tools")

# Un solo PlannerIA por proceso: reutiliza el cliente HTTP/IA entre llamadas.
_planner = PlannerIA()

_MODE = api_mode()

T = TypeVar("T")


async def _api_o_mock(nombre: str, fn_api: Callable[[], Awaitable[T]], fn_mock: Callable[[], T]) -> T:
    """Intenta la API real; ante cualquier fallo usa el mock (modo auto).

    En modo "api" el error se propaga; en modo "mock" ni se intenta la API.
    """
    if _MODE == "mock":
        return fn_mock()
    try:
        return await fn_api()
    except Exception as exc:
        if _MODE == "api":
            raise
        logger.warning("API falló en '%s' (%r), usando mock", nombre, exc)
        return fn_mock()


def _perfil_desde_prefs(prefs: dict) -> AccessibilityProfile:
    """Deriva el perfil igual que el mock del usuario semilla: con
    alto contraste + objetivos grandes se asume discapacidad visual."""
    if prefs.get("highContrast") and prefs.get("largeTargets"):
        return AccessibilityProfile.VISUAL_IMPAIRMENT
    return AccessibilityProfile.DEFAULT


async def get_user_context(id_user: int) -> UserContext:
    """Devuelve el perfil del usuario y sus preferencias de accesibilidad.
    Equivale a GET /users/me + GET /me/preferences."""
    logger.info("Tool 'get_user_context' invocada (id_user=%s)", id_user)

    async def _api() -> Optional[UserContext]:
        me = await call_api(lambda c: c.get_user_me())
        if me.get("idUser") != id_user:
            return None
        prefs = await call_api(lambda c: c.get_me_preferences())
        accessibility = AccessibilityPreference.model_validate(prefs)
        accessibility.accessibility_profile = _perfil_desde_prefs(prefs)
        return UserContext.model_validate({**me, "accessibility": accessibility})

    context = await _api_o_mock(
        "get_user_context",
        _api,
        lambda: mock_data.mock_get_user_context(id_user),
    )
    if context is None:
        raise ValueError(f"Usuario no encontrado: id_user={id_user}")
    return context


async def get_accounts(
        id_user: int,
        status: Optional[str] = None,
        account_type: Optional[str] = None,
) -> list[Account]:
    """Devuelve las cuentas del usuario, opcionalmente filtradas por
    status ('active'/'blocked') o accountType ('debito'/'credito').
    Equivale a GET /accounts."""
    logger.info(
        "Tool 'get_accounts' invocada (id_user=%s, status=%s, account_type=%s)",
        id_user, status, account_type,
    )
    # La API identifica al usuario por el JWT, no por id_user: solo el
    # usuario semilla (id 1, el del login automático) tiene datos reales.
    return await _api_o_mock(
        "get_accounts",
        lambda: _api_lista(Account, lambda c: c.get_accounts(status, account_type)) if id_user == 1 else _sin_api(),
        lambda: mock_data.mock_get_accounts(id_user, status, account_type),
    )


async def _sin_api():
    raise RuntimeError("sin sesión API para este usuario, usando mock")


async def _api_lista(modelo, llamada):
    datos = await call_api(llamada)
    return [modelo.model_validate(item) for item in datos]


async def get_account_summary(id_user: int) -> AccountSummary:
    """Devuelve el saldo total del usuario y el desglose por cuenta.
    Equivale a GET /me/account-summary."""
    logger.info("Tool 'get_account_summary' invocada (id_user=%s)", id_user)
    return await _api_o_mock(
        "get_account_summary",
        lambda: _api_uno(AccountSummary, lambda c: c.get_account_summary()) if id_user == 1 else _sin_api(),
        lambda: mock_data.mock_get_account_summary(id_user),
    )


async def _api_uno(modelo, llamada):
    datos = await call_api(llamada)
    return modelo.model_validate(datos)


async def get_account_detail(id_account: int) -> Account:
    """Devuelve el detalle de una sola cuenta. Equivale a
    GET /accounts/{accountId}."""
    logger.info("Tool 'get_account_detail' invocada (id_account=%s)", id_account)
    account = await _api_o_mock(
        "get_account_detail",
        lambda: _api_uno_o_none(Account, lambda c: c.get_account(id_account)),
        lambda: mock_data.mock_get_account_detail(id_account),
    )
    if account is None:
        raise ValueError(f"Cuenta no encontrada: id_account={id_account}")
    return account


async def _api_uno_o_none(modelo, llamada):
    from app.integration.api_client import BancaApiError
    try:
        datos = await call_api(llamada)
    except BancaApiError as exc:
        if exc.status_code == 404:
            return None
        raise
    return modelo.model_validate(datos)


async def get_transactions(
        id_account: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        category: Optional[str] = None,
        expense_category: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
) -> list[Transaction]:
    """Devuelve los movimientos de una cuenta, opcionalmente filtrados por
    rango de fecha, categoría, dirección, estado o texto de búsqueda.
    Equivale a GET /accounts/{accountId}/transactions."""
    logger.info(
        "Tool 'get_transactions' invocada (id_account=%s, date_from=%s, date_to=%s, "
        "category=%s, expense_category=%s, direction=%s, status=%s, search=%s, limit=%d)",
        id_account, date_from, date_to, category, expense_category, direction, status, search, limit,
    )
    return await _api_o_mock(
        "get_transactions",
        lambda: _api_lista(
            Transaction,
            lambda c: c.get_account_transactions(
                id_account, date_from, date_to, category, expense_category,
                direction, status, search, limit,
            ),
        ),
        lambda: mock_data.mock_get_transactions(
            id_account, date_from, date_to, category, expense_category, direction, status, search, limit
        ),
    )


async def get_all_transactions(
        id_user: int,
        id_account: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        category: Optional[str] = None,
        expense_category: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
) -> list[Transaction]:
    """Devuelve los movimientos de TODAS las cuentas del usuario (búsqueda
    transversal), con los mismos filtros que get_transactions más un
    id_account opcional. Equivale a GET /me/transactions."""
    logger.info(
        "Tool 'get_all_transactions' invocada (id_user=%s, id_account=%s, limit=%d)",
        id_user, id_account, limit,
    )
    return await _api_o_mock(
        "get_all_transactions",
        lambda: _api_lista(
            Transaction,
            lambda c: c.get_all_transactions(
                date_from, date_to, category, expense_category,
                direction, status, search, limit, id_account,
            ),
        ) if id_user == 1 else _sin_api(),
        lambda: mock_data.mock_get_all_transactions(
            id_user, id_account, date_from, date_to, category, expense_category, direction, status, search, limit
        ),
    )


async def get_daily_balance(
        id_account: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
) -> list[DailyBalance]:
    """Devuelve el balance diario de una cuenta. Equivale a
    GET /accounts/{accountId}/daily-balances."""
    logger.info("Tool 'get_daily_balance' invocada (id_account=%s)", id_account)
    return await _api_o_mock(
        "get_daily_balance",
        lambda: _api_lista(
            DailyBalance,
            lambda c: c.get_account_daily_balances(id_account, date_from, date_to),
        ),
        lambda: mock_data.mock_get_daily_balance(id_account, date_from, date_to),
    )


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

    async def _api() -> Transfer:
        # La API exige destinationMasked (mock_data lo generaba igual);
        # el idempotencyKey evita duplicados si se reintenta la red.
        masked = "****" + uuid.uuid4().hex[:4].upper()
        datos = await call_api(
            lambda c: c.create_transfer(
                id_origin_account, destination_alias, masked, amount,
                currency, concept, str(uuid.uuid4()),
            )
        )
        return Transfer.model_validate(datos)

    return await _api_o_mock(
        "prepare_transfer",
        _api,
        lambda: mock_data.mock_prepare_transfer(
            id_user, id_origin_account, destination_alias, amount, currency, concept
        ),
    )


async def confirm_transfer(id_transfer: int, method: str = "app") -> Transfer:
    """Confirma una transferencia previamente creada con prepare_transfer.
    Equivale a POST /transfers/{transferId}/confirm."""
    logger.info("Tool 'confirm_transfer' invocada (id_transfer=%s, method=%s)", id_transfer, method)

    async def _api() -> Optional[Transfer]:
        from app.integration.api_client import BancaApiError
        try:
            datos = await call_api(lambda c: c.confirm_transfer(id_transfer, method))
        except BancaApiError as exc:
            if exc.status_code == 404:
                return None
            raise
        # La API devuelve {"transfer": {...}, "confirmation": {...}}.
        transferencia = datos.get("transfer", datos)
        return Transfer.model_validate(transferencia)

    transfer = await _api_o_mock(
        "confirm_transfer",
        _api,
        lambda: mock_data.mock_confirm_transfer(id_transfer, method),
    )
    if transfer is None:
        raise ValueError(f"Transferencia no encontrada: id_transfer={id_transfer}")
    return transfer


async def get_transfers(
        id_user: Optional[int] = None,
        status: Optional[str] = None,
        id_origin_account: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20,
) -> list[Transfer]:
    """Devuelve el historial de transferencias del usuario, opcionalmente
    filtrado por estado, cuenta origen o rango de fecha. Equivale a
    GET /transfers."""
    logger.info(
        "Tool 'get_transfers' invocada (id_user=%s, status=%s, id_origin_account=%s, limit=%d)",
        id_user, status, id_origin_account, limit,
    )
    return await _api_o_mock(
        "get_transfers",
        lambda: _api_lista(
            Transfer,
            lambda c: c.get_transfers(status, id_origin_account, date_from, date_to, limit),
        ),
        lambda: mock_data.mock_get_transfers(id_user, status, id_origin_account, date_from, date_to, limit),
    )


async def get_transfer_detail(id_transfer: int) -> Transfer:
    """Devuelve el detalle de una transferencia. Equivale a
    GET /transfers/{transferId}."""
    logger.info("Tool 'get_transfer_detail' invocada (id_transfer=%s)", id_transfer)
    transfer = await _api_o_mock(
        "get_transfer_detail",
        lambda: _api_uno_o_none(Transfer, lambda c: c.get_transfer(id_transfer)),
        lambda: mock_data.mock_get_transfer_detail(id_transfer),
    )
    if transfer is None:
        raise ValueError(f"Transferencia no encontrada: id_transfer={id_transfer}")
    return transfer


async def get_reconciliation_status(
        id_user: Optional[int] = None,
        id_transfer: Optional[int] = None,
        id_account: Optional[int] = None,
        status: Optional[str] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliación entre transferencias y
    movimientos, opcionalmente filtrado por estado. Equivale a
    GET /reconciliation."""
    logger.info(
        "Tool 'get_reconciliation_status' invocada (id_user=%s, id_transfer=%s, id_account=%s, status=%s)",
        id_user, id_transfer, id_account, status,
    )
    matches = await _api_o_mock(
        "get_reconciliation_status",
        lambda: _api_lista(ReconciliationMatch, lambda c: c.get_reconciliation(status)),
        lambda: mock_data.mock_get_reconciliation_status(id_user, id_transfer, id_account),
    )
    if id_transfer is not None:
        matches = [m for m in matches if m.id_transfer == id_transfer]
    return matches


async def get_statements(
        id_account: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
        status: Optional[str] = None,
) -> list[Statement]:
    """Devuelve los estados de cuenta de una cuenta, opcionalmente
    filtrados por año/mes/estado. Equivale a
    GET /accounts/{accountId}/statements."""
    logger.info(
        "Tool 'get_statements' invocada (id_account=%s, year=%s, month=%s, status=%s)",
        id_account, year, month, status,
    )
    return await _api_o_mock(
        "get_statements",
        lambda: _api_lista(
            Statement, lambda c: c.get_statements(id_account, year, month, status)
        ),
        lambda: mock_data.mock_get_statements(id_account, year, month, status),
    )


async def get_statement_detail(id_account: int, id_statement: int) -> StatementDetail:
    """Devuelve el detalle y desglose de gastos de un estado de cuenta.
    Equivale a GET /accounts/{accountId}/statements/{statementId}."""
    logger.info(
        "Tool 'get_statement_detail' invocada (id_account=%s, id_statement=%s)",
        id_account, id_statement,
    )
    detalle = await _api_o_mock(
        "get_statement_detail",
        lambda: _api_uno_o_none(
            StatementDetail, lambda c: c.get_statement_detail(id_account, id_statement)
        ),
        lambda: mock_data.mock_get_statement_detail(id_account, id_statement),
    )
    if detalle is None:
        raise ValueError(f"Estado de cuenta no encontrado: id_account={id_account}, id_statement={id_statement}")
    return detalle


async def get_expense_categories(
        search: Optional[str] = None, id_account: Optional[int] = None
) -> list[ExpenseCategory]:
    """Devuelve las categorías de gasto CON el monto y número de movimientos
    débito de cada una en la cuenta (no solo el nombre): úsala para
    responder "en qué gasté mi dinero" / "gastos por categoría" / desglose
    de gasto. Equivale a GET /expense-categories + agregación de
    GET /accounts/{accountId}/transactions."""
    logger.info("Tool 'get_expense_categories' invocada (search=%s, id_account=%s)", search, id_account)
    cuenta = id_account or 1

    async def _api() -> list[ExpenseCategory]:
        categorias = await _api_lista(ExpenseCategory, lambda c: c.get_expense_categories(search))
        movimientos = await _api_lista(
            Transaction,
            lambda c: c.get_account_transactions(
                cuenta, None, None, None, None, "debit", None, None, 500
            ),
        )
        # La API real clasifica el gasto por id_expense_category (FK real,
        # ver DbSeeder.cs). El texto libre "category" del movimiento (ej.
        # "super") NO calza contra el code del catálogo (ej. "supermarket"),
        # así que agregamos por id y, solo si un movimiento no trae FK,
        # caemos a comparar por texto/código como respaldo.
        por_id: dict[int, tuple[float, int]] = {}
        por_code: dict[str, tuple[float, int]] = {}
        for t in movimientos:
            if t.id_expense_category is not None:
                monto, conteo = por_id.get(t.id_expense_category, (0.0, 0))
                por_id[t.id_expense_category] = (monto + t.amount, conteo + 1)
            else:
                monto, conteo = por_code.get(t.category, (0.0, 0))
                por_code[t.category] = (monto + t.amount, conteo + 1)

        def _agregado(c: ExpenseCategory) -> tuple[float, int]:
            if c.id_category in por_id:
                return por_id[c.id_category]
            return por_code.get(c.code, (0.0, 0))

        return [
            c.model_copy(
                update={"total_amount": _agregado(c)[0], "transaction_count": _agregado(c)[1]}
            )
            for c in categorias
        ]

    return await _api_o_mock(
        "get_expense_categories",
        _api,
        lambda: mock_data.mock_get_expense_categories(search),
    )


async def get_budgets_monthly(
        year: int,
        month: int,
        category: Optional[str] = None,
        status: Optional[str] = None,
) -> BudgetMonthlySummary:
    """Devuelve el resumen mensual de presupuestos (límite, gastado y %
    de avance por categoría). Equivale a GET /me/budgets/monthly."""
    logger.info(
        "Tool 'get_budgets_monthly' invocada (year=%d, month=%d, category=%s, status=%s)",
        year, month, category, status,
    )
    return await _api_o_mock(
        "get_budgets_monthly",
        lambda: _api_uno(
            BudgetMonthlySummary,
            lambda c: c.get_budgets_monthly(year, month, category, status),
        ),
        lambda: mock_data.mock_get_budgets_monthly(year, month, category, status),
    )


async def get_savings_goals(status: Optional[str] = None) -> list[SavingsGoal]:
    """Devuelve las metas de ahorro del usuario, opcionalmente filtradas
    por estado. Equivale a GET /me/savings-goals."""
    logger.info("Tool 'get_savings_goals' invocada (status=%s)", status)
    return await _api_o_mock(
        "get_savings_goals",
        lambda: _api_lista(SavingsGoal, lambda c: c.get_savings_goals(status)),
        lambda: mock_data.mock_get_savings_goals(status),
    )


async def get_credit_cards(status: Optional[str] = None) -> list[CreditCard]:
    """Devuelve las tarjetas de crédito del usuario, opcionalmente
    filtradas por estado. Equivale a GET /me/credit-cards."""
    logger.info("Tool 'get_credit_cards' invocada (status=%s)", status)
    return await _api_o_mock(
        "get_credit_cards",
        lambda: _api_lista(CreditCard, lambda c: c.get_credit_cards(status)),
        lambda: mock_data.mock_get_credit_cards(status),
    )


async def get_credit_card_statements(
        id_credit_card: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
) -> list[CreditCardStatement]:
    """Devuelve los estados de cuenta de una tarjeta de crédito,
    opcionalmente filtrados por año/mes. Equivale a
    GET /me/credit-cards/{cardId}/statements."""
    logger.info(
        "Tool 'get_credit_card_statements' invocada (id_credit_card=%s, year=%s, month=%s)",
        id_credit_card, year, month,
    )
    return await _api_o_mock(
        "get_credit_card_statements",
        lambda: _api_lista(
            CreditCardStatement,
            lambda c: c.get_credit_card_statements(id_credit_card, year, month),
        ),
        lambda: mock_data.mock_get_credit_card_statements(id_credit_card, year, month),
    )


async def planificar_accion(mensaje_usuario: str, contexto: Optional[dict] = None) -> ActionPlan:
    """
    Genera un plan de acción tipado (ActionPlan) a partir de la intención
    del usuario, indicando qué tools de las de arriba (ver TOOL_NAMES en
    schemas.py) conviene invocar, con qué argumentos (IDs enteros reales o
    null) y con qué "ui_hint" debería mostrarse cada paso en la interfaz.

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