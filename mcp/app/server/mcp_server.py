"""
Servidor MCP — parte de Guillermo (MCP + modelo de IA).

Qué expone este servidor (sección 5 del resumen — "Tools ejemplo",
ampliado con los endpoints nuevos de Pablo — ver docs/datos/06-catalogo-
ia-placeholders.md):
  1. Las tools de datos, cada una con entrada y salida tipadas (Pydantic,
     en schemas/schemas.py, ver TOOL_NAMES) y respaldadas por mocks
     (placeholders/mock_data.py, alineados 1:1 al seed real de Pablo)
     hasta que Cain conecte integration/api_client.py. Todas de SOLO
     LECTURA salvo prepare_transfer/confirm_transfer:
       - get_user_context, get_accounts, get_account_summary,
         get_account_detail
       - get_transactions, get_all_transactions, get_daily_balance
       - search_memory_context (sigue mock: sin endpoint real todavía)
       - prepare_transfer, confirm_transfer
       - get_transfers, get_transfer_detail, get_reconciliation_status
       - get_statements, get_statement_detail, get_expense_categories
       - get_budgets_monthly, get_savings_goals
       - get_credit_cards, get_credit_card_statements
  2. Una tool adicional de orquestación con IA, `planificar_accion`, que le
     pide a la IA un ActionPlan (schemas.py) indicando qué tools de las de
     arriba conviene invocar para cumplir la intención del usuario, con qué
     argumentos (IDs enteros reales o null) y con qué "ui_hint" debería
     mostrarse cada paso en la interfaz.

Las implementaciones viven en tools/tools.py (funciones planas, fáciles de
probar sin levantar FastMCP); aquí solo se registran con `@mcp.tool()`.

Uso (desde la carpeta mcp/, con el venv activo):
    python -m app.server.mcp_server
"""

import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# Este archivo se lanza como script (`python app/server/mcp_server.py`, ya
# sea directo o vía fastmcp.Client desde mcp_client.py). Python solo agrega
# al sys.path la carpeta del propio script (app/server/), no la raíz del
# paquete `app` (mcp/), así que sin esto "from app import ..." fallaría con
# ModuleNotFoundError salvo que ya se ejecute con `python -m app.server.mcp_server`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

# Debe cargarse ANTES de importar app.ia.ia_client (vía tools.py), porque
# ese módulo lee DEEPSEEK_API_KEY con os.getenv() apenas se importa.
load_dotenv()

from fastmcp import FastMCP

from app import tools
from app.logging_config import setup_logging
from app.schemas import (
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
async def get_accounts(
    id_user: int,
    status: Optional[str] = None,
    account_type: Optional[str] = None,
) -> list[Account]:
    """Devuelve las cuentas del usuario, opcionalmente filtradas por
    status ('active'/'blocked') o accountType ('debito'/'credito').
    Equivale a GET /accounts."""
    return await tools.get_accounts(id_user, status, account_type)


@mcp.tool()
async def get_account_summary(id_user: int) -> AccountSummary:
    """Devuelve el saldo total del usuario y el desglose por cuenta.
    Equivale a GET /me/account-summary."""
    return await tools.get_account_summary(id_user)


@mcp.tool()
async def get_account_detail(id_account: int) -> Account:
    """Devuelve el detalle de una sola cuenta. Equivale a
    GET /accounts/{accountId}."""
    return await tools.get_account_detail(id_account)


@mcp.tool()
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
    return await tools.get_transactions(
        id_account, date_from, date_to, category, expense_category, direction, status, search, limit
    )


@mcp.tool()
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
    transversal). Equivale a GET /me/transactions."""
    return await tools.get_all_transactions(
        id_user, id_account, date_from, date_to, category, expense_category, direction, status, search, limit
    )


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
    return await tools.get_transfers(id_user, status, id_origin_account, date_from, date_to, limit)


@mcp.tool()
async def get_transfer_detail(id_transfer: int) -> Transfer:
    """Devuelve el detalle de una transferencia. Equivale a
    GET /transfers/{transferId}."""
    return await tools.get_transfer_detail(id_transfer)


@mcp.tool()
async def get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
    status: Optional[str] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliación entre transferencias y
    movimientos, opcionalmente filtrado por estado. Equivale a
    GET /reconciliation."""
    return await tools.get_reconciliation_status(id_user, id_transfer, id_account, status)


@mcp.tool()
async def get_statements(
    id_account: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[str] = None,
) -> list[Statement]:
    """Devuelve los estados de cuenta de una cuenta, opcionalmente
    filtrados por año/mes/estado. Equivale a
    GET /accounts/{accountId}/statements."""
    return await tools.get_statements(id_account, year, month, status)


@mcp.tool()
async def get_statement_detail(id_account: int, id_statement: int) -> StatementDetail:
    """Devuelve el detalle y desglose de gastos de un estado de cuenta.
    Equivale a GET /accounts/{accountId}/statements/{statementId}."""
    return await tools.get_statement_detail(id_account, id_statement)


@mcp.tool()
async def get_expense_categories(
    search: Optional[str] = None, id_account: Optional[int] = None
) -> list[ExpenseCategory]:
    """Devuelve las categorías de gasto CON el monto y el número de
    movimientos débito de cada una (total_amount, transaction_count).
    Úsala para "en qué gasté mi dinero", "gastos por categoría" o
    cualquier desglose de gasto. Equivale a GET /expense-categories +
    agregación de GET /accounts/{accountId}/transactions."""
    return await tools.get_expense_categories(search, id_account)


@mcp.tool()
async def get_budgets_monthly(
    year: int,
    month: int,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> BudgetMonthlySummary:
    """Devuelve el resumen mensual de presupuestos. Equivale a
    GET /me/budgets/monthly."""
    return await tools.get_budgets_monthly(year, month, category, status)


@mcp.tool()
async def get_savings_goals(status: Optional[str] = None) -> list[SavingsGoal]:
    """Devuelve las metas de ahorro del usuario, opcionalmente filtradas
    por estado. Equivale a GET /me/savings-goals."""
    return await tools.get_savings_goals(status)


@mcp.tool()
async def get_credit_cards(status: Optional[str] = None) -> list[CreditCard]:
    """Devuelve las tarjetas de crédito del usuario, opcionalmente
    filtradas por estado. Equivale a GET /me/credit-cards."""
    return await tools.get_credit_cards(status)


@mcp.tool()
async def get_credit_card_statements(
    id_credit_card: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> list[CreditCardStatement]:
    """Devuelve los estados de cuenta de una tarjeta de crédito,
    opcionalmente filtrados por año/mes. Equivale a
    GET /me/credit-cards/{cardId}/statements."""
    return await tools.get_credit_card_statements(id_credit_card, year, month)


# ---------------------------------------------------------------------------
# TOOL DE ORQUESTACIÓN CON IA
# ---------------------------------------------------------------------------
@mcp.tool()
async def planificar_accion(mensaje_usuario: str, contexto: Optional[dict] = None) -> ActionPlan:
    """
    Genera un plan de acción tipado (ActionPlan) a partir de la intención
    del usuario, indicando qué tools de las de arriba conviene invocar,
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
    import os as _os

    # Transporte configurable: stdio (default, lo que usa el puente
    # Next.js en dev y mcp_client.py) o streamable-http en docker
    # (MCP_TRANSPORT=http, puerto MCP_PORT, default 8080). Ver
    # docs/frontend/07-puente-mcp-frontend.md (opción HTTP futura).
    _transport = _os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    if "--http" in sys.argv:
        _transport = "http"
    if _transport == "http":
        _port = int(_os.getenv("MCP_PORT", "8080"))
        logger.info("Arrancando servidor MCP en modo streamable-http (puerto %d)", _port)
        mcp.run(transport="streamable-http", host="0.0.0.0", port=_port)
    else:
        logger.info("Arrancando servidor MCP en modo stdio")
        mcp.run(transport="stdio")
