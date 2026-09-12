"""
Mocks / placeholders — parte de Guillermo (MCP + modelo de IA).

MIGRACIÓN A LA BASE DE DATOS REAL (Reto-Banorte / BancaAdaptativa.Api):
-------------------------------------------------------------------------
Antes estos mocks devolvían strings mágicos tipo "__PLACEHOLDER_USER_ID__"
porque no existían IDs reales con los que alinearse. Ahora sí existe el
backend real de Pablo (con su seed en Data/DbSeeder.cs), así que estos
mocks dejan de inventar texto y en su lugar **reflejan exactamente los
datos que siembra DbSeeder.cs** para el usuario demo:

    Usuario id=1  demo@banorte.mx  "Usuario Demo"  (perfil: discapacidad visual)
    Cuenta  id=1  "Nómina"  debito  ****1234  saldo 25,400.50 MXN
    Transacciones: nómina (+15,000), súper (-850.75), transporte (-320)
    Balance diario: apertura 26,000 / cierre 24,829.25
    Transferencia id=1: $2,000 a "Mamá" (****5678), status=pending

Esto es intencional: así Cain puede probar la integración comparando
1:1 el JSON que da este mock contra el JSON que da la API real corriendo
con el seed de fábrica, sin tener que adivinar qué IDs usar.

Regla de oro para que Cain pueda reemplazar esto sin dolor: cada función
mock_* tiene la MISMA firma y el MISMO tipo de retorno (los modelos de
schemas.py) que tendrá la llamada real a la API cuando exista. El día que
Cain conecte integration/api_client.py, solo cambia el CUERPO de estas
funciones por un `await client.get_...(...)` — no cambia ni las firmas ni
lo que usa server/mcp_server.py (vía tools/tools.py).

Cain puede ubicar rápido qué sigue siendo mock buscando:
- El campo "x_placeholder": true en cualquier respuesta.
- Los endpoints que en schemas.py están marcados como "aún sin endpoint
  real" (MemoryEvent, AuditLog): esos siguen mock aunque Pablo entregue
  todo lo demás, porque el endpoint /memory/query no existe todavía en
  Endpoints/*.cs.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from app.schemas import (
    Account,
    AccessibilityPreference,
    AccessibilityProfile,
    AccountSummary,
    Budget,
    BudgetMonthlySummary,
    CreditCard,
    CreditCardStatement,
    DailyBalance,
    ExpenseCategory,
    ReconciliationMatch,
    SavingsGoal,
    Statement,
    StatementDetail,
    StatementExpenseBreakdown,
    Transaction,
    Transfer,
    TransferStatus,
    UserContext,
)

# ---------------------------------------------------------------------------
# "Ahora" fijo para que los mocks sean deterministas en demos/pruebas.
# ---------------------------------------------------------------------------
_NOW = datetime(2026, 9, 12, 12, 0, 0)
_HOY = date(2026, 9, 12)

# ---------------------------------------------------------------------------
# USUARIO SEMILLA (id_user=1) — espejo exacto de DbSeeder.Seed()
# ---------------------------------------------------------------------------
_USER_DEMO = UserContext(
    id_user=1,
    name="Usuario Demo",
    email="demo@banorte.mx",
    locale="es-MX",
    status="active",
    accessibility=AccessibilityPreference(
        id_preference=1,
        font_scale=1.25,
        high_contrast=True,
        dark_mode=False,
        reduced_motion=True,
        large_targets=True,
        plain_language=True,
        updated_at=_NOW,
        # Derivado por nosotros a partir de UserProfile.disability_type="visual"
        # (DbSeeder.cs) + estas preferencias, para elegir qué bloque de
        # "messages" del ActionPlan mostrarle a este usuario.
        accessibility_profile=AccessibilityProfile.VISUAL_IMPAIRMENT,
    ),
    x_placeholder=True,
)

# ---------------------------------------------------------------------------
# CUENTAS (id_account=1) — espejo de DbSeeder.Seed()
# ---------------------------------------------------------------------------
_ACCOUNTS: list[Account] = [
    Account(
        id_account=1,
        account_type="debito",
        alias="Nómina",
        masked_number="****1234",
        currency="MXN",
        balance=25400.50,
        status="active",
        created_at=_NOW - timedelta(days=1),
        x_placeholder=True,
    ),
]

# ---------------------------------------------------------------------------
# TRANSACCIONES (id_account=1) — espejo de DbSeeder.Seed()
# ---------------------------------------------------------------------------
_TRANSACTIONS: list[Transaction] = [
    Transaction(
        id_transaction=1,
        date=_HOY - timedelta(days=2),
        amount=15000.0,
        direction="credit",
        category="nomina",
        description="Pago nómina",
        status="posted",
        reference="NOM-001",
        x_placeholder=True,
    ),
    Transaction(
        id_transaction=2,
        date=_HOY - timedelta(days=1),
        amount=850.75,
        direction="debit",
        category="super",
        description="Súper",
        status="posted",
        reference="SUP-002",
        x_placeholder=True,
    ),
    Transaction(
        id_transaction=3,
        date=_HOY,
        amount=320.0,
        direction="debit",
        category="transporte",
        description="Transporte",
        status="posted",
        reference="TRN-003",
        x_placeholder=True,
    ),
]
# A qué cuenta pertenece cada transacción/balance/transferencia — el mock
# solo tiene una cuenta sembrada (id_account=1), igual que DbSeeder.cs.
_ACCOUNT_ID_DEMO = 1

# ---------------------------------------------------------------------------
# BALANCE DIARIO (id_account=1) — espejo de DbSeeder.Seed()
# ---------------------------------------------------------------------------
_DAILY_BALANCES: list[DailyBalance] = [
    DailyBalance(
        id_balance=1,
        date=_HOY,
        opening_balance=26000.0,
        income=0.0,
        expenses=1170.75,
        closing_balance=24829.25,
        x_placeholder=True,
    ),
]

# Transferencias y conciliaciones: parte fija (la del seed) + dinámicas
# (creadas en memoria por prepare_transfer/confirm_transfer durante la demo).
_TRANSFERS: dict[int, Transfer] = {
    1: Transfer(
        id_transfer=1,
        id_origin_account=1,
        destination_alias="Mamá",
        destination_masked="****5678",
        amount=2000.0,
        currency="MXN",
        concept="Apoyo",
        status="pending",
        idempotency_key=str(uuid.uuid4()),
        confirmed_at=None,
        x_placeholder=True,
    ),
}
_RECONCILIATIONS: dict[int, ReconciliationMatch] = {}
_NEXT_TRANSFER_ID = 2  # el 1 ya lo usa el seed

# ---------------------------------------------------------------------------
# CATEGORÍAS DE GASTO — espejo aproximado del catálogo por defecto que
# DbSeeder.cs siembra (nombre/código en español, igual que Transaction.category
# de arriba: "nomina", "super", "transporte").
# ---------------------------------------------------------------------------
_EXPENSE_CATEGORIES: list[ExpenseCategory] = [
    ExpenseCategory(id_category=1, name="Nómina", code="nomina", icon="wallet", is_default=True, sort_order=1, x_placeholder=True),
    ExpenseCategory(id_category=2, name="Súper", code="super", icon="shopping-cart", is_default=True, sort_order=2, x_placeholder=True),
    ExpenseCategory(id_category=3, name="Transporte", code="transporte", icon="bus", is_default=True, sort_order=3, x_placeholder=True),
]

# ---------------------------------------------------------------------------
# ESTADOS DE CUENTA (por id_account=1) — aún no hay estados de cuenta
# generados en el seed base de Pablo, así que este mock arranca vacío y
# solo existe para que la tool tenga a qué responder (lista vacía, no error).
# ---------------------------------------------------------------------------
_STATEMENTS: dict[int, Statement] = {}
_STATEMENT_EXPENSES: dict[int, list[StatementExpenseBreakdown]] = {}

# ---------------------------------------------------------------------------
# PRESUPUESTOS — sin seed real todavía (Pablo aún no siembra Budget en
# DbSeeder.cs); placeholder de un presupuesto de ejemplo para el mes/año
# "de hoy" (_HOY), sobre la categoría "super".
# ---------------------------------------------------------------------------
_BUDGETS: list[Budget] = [
    Budget(
        id_budget=1,
        id_expense_category=2,
        category_name="Súper",
        category_code="super",
        month=_HOY.month,
        year=_HOY.year,
        amount_limit=3000.0,
        current_spent=850.75,
        usage_percent=round(850.75 / 3000.0 * 100, 2),
        status="active",
        x_placeholder=True,
    ),
]

# ---------------------------------------------------------------------------
# METAS DE AHORRO — sin seed real todavía; una meta de ejemplo.
# ---------------------------------------------------------------------------
_SAVINGS_GOALS: list[SavingsGoal] = [
    SavingsGoal(
        id_goal=1,
        name="Vacaciones",
        target_amount=15000.0,
        current_amount=3200.0,
        progress_percent=round(3200.0 / 15000.0 * 100, 2),
        target_date=_NOW + timedelta(days=180),
        status="active",
        created_at=_NOW - timedelta(days=30),
        updated_at=_NOW - timedelta(days=1),
        x_placeholder=True,
    ),
]

# ---------------------------------------------------------------------------
# TARJETAS DE CRÉDITO — sin seed real todavía; una tarjeta de ejemplo.
# ---------------------------------------------------------------------------
_CREDIT_CARDS: list[CreditCard] = [
    CreditCard(
        id_credit_card=1,
        card_number_masked="****9012",
        card_type="credito",
        credit_limit=20000.0,
        available_credit=17500.0,
        interest_rate=42.5,
        statement_cut_off_day=20,
        payment_due_day=5,
        status="active",
        created_at=_NOW - timedelta(days=180),
        x_placeholder=True,
    ),
]
_CREDIT_CARD_STATEMENTS: dict[int, list[CreditCardStatement]] = {}


# ---------------------------------------------------------------------------
# Funciones mock — misma firma/retorno que tendrán las llamadas reales de
# integration/api_client.py (BancaApiClient) cuando Cain las conecte.
# ---------------------------------------------------------------------------
def mock_get_user_context(id_user: int) -> Optional[UserContext]:
    """Devuelve el usuario semilla si id_user coincide (o si no se sabe
    cuál es, se sigue devolviendo el único usuario demo). Cain reemplazará
    el cuerpo por `await client.get_user_me()` + `await client.get_me_preferences()`."""
    if id_user not in (None, _USER_DEMO.id_user):
        return None
    return _USER_DEMO


def mock_get_accounts(
    id_user: int,
    status: Optional[str] = None,
    account_type: Optional[str] = None,
) -> list[Account]:
    """Cain reemplazará el cuerpo por
    `await client.get_accounts()` (Pablo agregó filtros ?status &
    ?accountType a GET /accounts; falta agregarlos a api_client.get_accounts
    cuando se conecte de verdad)."""
    items = list(_ACCOUNTS)
    if status:
        items = [a for a in items if a.status == status]
    if account_type:
        items = [a for a in items if a.account_type == account_type]
    return items


def mock_get_account_summary(id_user: int) -> AccountSummary:
    """Placeholder de GET /me/account-summary. Cain reemplazará el cuerpo
    por un método nuevo de `BancaApiClient` (aún no existe en
    integration/api_client.py) que llame a ese endpoint."""
    cuentas = _ACCOUNTS
    total = sum(a.balance for a in cuentas)
    moneda = cuentas[0].currency if cuentas else "MXN"
    return AccountSummary(total_balance=total, currency=moneda, accounts=cuentas, x_placeholder=True)


def mock_get_account_detail(id_account: int) -> Optional[Account]:
    """Placeholder de GET /accounts/{accountId}. Cain reemplazará el
    cuerpo por `await client.get_account(id_account)`."""
    for cuenta in _ACCOUNTS:
        if cuenta.id_account == id_account:
            return cuenta
    return None


def mock_get_transactions(
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
    """Cain reemplazará el cuerpo por
    `await client.get_account_transactions(id_account, date_from, date_to,
    category=category, direction=direction, status=status, search=search,
    limit=limit)` (falta agregar expenseCategory a api_client.py)."""
    if id_account != _ACCOUNT_ID_DEMO:
        return []
    return _filtrar_transacciones(
        _TRANSACTIONS, date_from, date_to, category, expense_category, direction, status, search
    )[:limit]


def mock_get_all_transactions(
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
    """Placeholder de GET /me/transactions (movimientos de TODAS las
    cuentas del usuario). Cain reemplazará el cuerpo por un método nuevo
    de `BancaApiClient` que llame a ese endpoint. El seed solo tiene una
    cuenta (id_account=1), así que hoy da el mismo resultado que
    mock_get_transactions salvo que aquí id_account es opcional."""
    if id_account is not None and id_account != _ACCOUNT_ID_DEMO:
        return []
    return _filtrar_transacciones(
        _TRANSACTIONS, date_from, date_to, category, expense_category, direction, status, search
    )[:limit]


def _filtrar_transacciones(
    items: list[Transaction],
    date_from: Optional[date],
    date_to: Optional[date],
    category: Optional[str],
    expense_category: Optional[str],
    direction: Optional[str],
    status: Optional[str],
    search: Optional[str],
) -> list[Transaction]:
    """Filtro compartido entre get_transactions y get_all_transactions
    (mismos query params en ambos endpoints reales)."""
    resultado = list(items)
    if date_from:
        resultado = [t for t in resultado if t.date >= date_from]
    if date_to:
        resultado = [t for t in resultado if t.date <= date_to]
    if category:
        resultado = [t for t in resultado if t.category == category]
    if expense_category:
        resultado = [t for t in resultado if t.category == expense_category]
    if direction:
        resultado = [t for t in resultado if t.direction == direction]
    if status:
        resultado = [t for t in resultado if t.status == status]
    if search:
        texto = search.lower()
        resultado = [t for t in resultado if texto in t.description.lower()]
    return resultado


def mock_get_daily_balance(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[DailyBalance]:
    """Cain reemplazará el cuerpo por
    `await client.get_account_daily_balances(id_account, date_from, date_to)`."""
    if id_account != _ACCOUNT_ID_DEMO:
        return []

    items = list(_DAILY_BALANCES)
    if date_from:
        items = [b for b in items if b.date >= date_from]
    if date_to:
        items = [b for b in items if b.date <= date_to]
    return items


def mock_search_memory_context(
    id_user: int,
    query: str,
    id_session: Optional[int] = None,
    limit: int = 10,
) -> list[dict]:
    """Placeholder de /memory/query. Pablo AÚN no expone ese endpoint en
    Endpoints/*.cs (ver MemoryEvent en schemas.py), así que esto sigue
    siendo mock incluso después de que el resto de la API esté conectada.
    Por ahora, sin eventos guardados, siempre devuelve lista vacía."""
    return []


def mock_prepare_transfer(
    id_user: int,
    id_origin_account: int,
    destination_alias: str,
    amount: float,
    currency: str = "MXN",
    concept: str = "",
) -> Transfer:
    """Crea un BORRADOR de transferencia (aún no confirmado). Cain
    reemplazará el cuerpo por
    `await client.create_transfer(id_origin_account, destination_alias, destination_masked, amount, currency, concept)`."""
    global _NEXT_TRANSFER_ID
    id_transfer = _NEXT_TRANSFER_ID
    _NEXT_TRANSFER_ID += 1

    transfer = Transfer(
        id_transfer=id_transfer,
        id_origin_account=id_origin_account,
        destination_alias=destination_alias,
        destination_masked="****" + uuid.uuid4().hex[:4].upper(),
        amount=amount,
        currency=currency,
        concept=concept,
        status=TransferStatus.PENDING_CONFIRMATION.value,
        idempotency_key=str(uuid.uuid4()),
        confirmed_at=None,
        x_placeholder=True,
    )
    _TRANSFERS[id_transfer] = transfer
    return transfer


def mock_confirm_transfer(id_transfer: int, method: str = "app") -> Optional[Transfer]:
    """Confirma una transferencia previamente creada. Cain reemplazará el
    cuerpo por `await client.confirm_transfer(id_transfer, method)`."""
    transfer = _TRANSFERS.get(id_transfer)
    if transfer is None:
        return None
    transfer.status = TransferStatus.CONFIRMED.value
    transfer.confirmed_at = _NOW
    return transfer


def mock_get_transfers(
    id_user: Optional[int] = None,
    status: Optional[str] = None,
    id_origin_account: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 20,
) -> list[Transfer]:
    """Placeholder de GET /transfers (historial). Cain reemplazará el
    cuerpo por `await client.get_transfers(...)` (falta agregar ese método
    de listado a api_client.py; hoy solo tiene create_transfer/get_transfer)."""
    items = list(_TRANSFERS.values())
    if status:
        items = [t for t in items if t.status == status]
    if id_origin_account is not None:
        items = [t for t in items if t.id_origin_account == id_origin_account]
    return items[:limit]


def mock_get_transfer_detail(id_transfer: int) -> Optional[Transfer]:
    """Placeholder de GET /transfers/{transferId}. Cain reemplazará el
    cuerpo por `await client.get_transfer(id_transfer)` (ya existe en
    api_client.py, solo falta conectarla aquí)."""
    return _TRANSFERS.get(id_transfer)


def mock_get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
    status: Optional[str] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliación entre transferencias y
    movimientos. Cain reemplazará el cuerpo por
    `await client.get_reconciliation()` (falta agregar el filtro ?status
    a ese método). El seed no trae conciliaciones todavía (la
    transferencia sembrada sigue 'pending')."""
    items = list(_RECONCILIATIONS.values())
    if id_transfer is not None:
        items = [r for r in items if r.id_transfer == id_transfer]
    if status:
        items = [r for r in items if r.status == status]
    return items


def mock_get_statements(
    id_account: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[str] = None,
) -> list[Statement]:
    """Placeholder de GET /accounts/{accountId}/statements. Cain
    reemplazará el cuerpo por un método nuevo de `BancaApiClient` que
    llame a ese endpoint. El seed base no genera estados de cuenta
    todavía (se generan bajo demanda vía POST .../statements/generate),
    así que este mock devuelve lista vacía hasta que existan."""
    items = [s for s in _STATEMENTS.values() if s.id_account == id_account]
    if year is not None:
        items = [s for s in items if s.period_start.year == year]
    if month is not None:
        items = [s for s in items if s.period_start.month == month]
    if status:
        items = [s for s in items if s.status == status]
    return items


def mock_get_statement_detail(id_account: int, id_statement: int) -> Optional[StatementDetail]:
    """Placeholder de GET /accounts/{accountId}/statements/{statementId}.
    Cain reemplazará el cuerpo por un método nuevo de `BancaApiClient`."""
    statement = _STATEMENTS.get(id_statement)
    if statement is None or statement.id_account != id_account:
        return None
    return StatementDetail(statement=statement, expenses=_STATEMENT_EXPENSES.get(id_statement, []))


def mock_get_expense_categories(search: Optional[str] = None) -> list[ExpenseCategory]:
    """Placeholder de GET /expense-categories. Cain reemplazará el cuerpo
    por un método nuevo de `BancaApiClient` que llame a ese endpoint."""
    items = list(_EXPENSE_CATEGORIES)
    if search:
        texto = search.lower()
        items = [c for c in items if texto in c.name.lower() or texto in c.code.lower()]
    return items


def mock_get_budgets_monthly(
    year: int,
    month: int,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> BudgetMonthlySummary:
    """Placeholder de GET /me/budgets/monthly. Cain reemplazará el cuerpo
    por un método nuevo de `BancaApiClient` que llame a ese endpoint."""
    items = [b for b in _BUDGETS if b.year == year and b.month == month]
    if category:
        items = [b for b in items if b.category_code == category]
    if status:
        items = [b for b in items if b.status == status]
    total_limit = sum(b.amount_limit for b in items)
    total_spent = sum(b.current_spent for b in items)
    return BudgetMonthlySummary(month=month, year=year, total_limit=total_limit, total_spent=total_spent, budgets=items)


def mock_get_savings_goals(status: Optional[str] = None) -> list[SavingsGoal]:
    """Placeholder de GET /me/savings-goals. Cain reemplazará el cuerpo
    por un método nuevo de `BancaApiClient` que llame a ese endpoint."""
    items = list(_SAVINGS_GOALS)
    if status:
        items = [g for g in items if g.status == status]
    return items


def mock_get_credit_cards(status: Optional[str] = None) -> list[CreditCard]:
    """Placeholder de GET /me/credit-cards. Cain reemplazará el cuerpo por
    un método nuevo de `BancaApiClient` que llame a ese endpoint."""
    items = list(_CREDIT_CARDS)
    if status:
        items = [c for c in items if c.status == status]
    return items


def mock_get_credit_card_statements(
    id_credit_card: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> list[CreditCardStatement]:
    """Placeholder de GET /me/credit-cards/{cardId}/statements. Cain
    reemplazará el cuerpo por un método nuevo de `BancaApiClient`. El seed
    base no genera estados de cuenta de tarjeta todavía (se generan bajo
    demanda vía POST .../statements/generate), así que este mock devuelve
    lista vacía hasta que existan."""
    items = _CREDIT_CARD_STATEMENTS.get(id_credit_card, [])
    if year is not None:
        items = [s for s in items if s.period_start.year == year]
    if month is not None:
        items = [s for s in items if s.period_start.month == month]
    return items


# ---------------------------------------------------------------------------
# UTILIDAD PARA CAIN: ubicar qué respuestas siguen siendo datos de demo
# ---------------------------------------------------------------------------
def find_placeholders(data) -> list[str]:
    """Recorre recursivamente una estructura de datos (dicts/lists, p.ej.
    el resultado de `modelo.model_dump()`) y devuelve las 'rutas' de todos
    los objetos marcados con 'x_placeholder': true.

    Con la migración a IDs enteros ya no hay strings mágicos tipo
    "__PLACEHOLDER_..." que buscar (ver STEP_ARGUMENT_PLACEHOLDER_DEFAULTS
    en schemas.py, casi vacío a propósito) — la señal ahora es el propio
    campo 'x_placeholder' que cada entidad ya trae.

    Uso:
        accounts = mock_get_accounts(1)
        find_placeholders([a.model_dump() for a in accounts])
        # ['[0]']  (índice del objeto marcado como placeholder)
    """
    encontrados: list[str] = []

    def _recorrer(nodo, ruta: str) -> None:
        if isinstance(nodo, dict):
            if nodo.get("x_placeholder") is True or nodo.get("xPlaceholder") is True:
                encontrados.append(ruta or "$")
            for clave, valor in nodo.items():
                _recorrer(valor, f"{ruta}.{clave}" if ruta else clave)
        elif isinstance(nodo, list):
            for i, item in enumerate(nodo):
                _recorrer(item, f"{ruta}[{i}]")

    _recorrer(data, "")
    return encontrados
