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
    DailyBalance,
    ReconciliationMatch,
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


def mock_get_accounts(id_user: int) -> list[Account]:
    """Cain reemplazará el cuerpo por `await client.get_accounts()`."""
    return _ACCOUNTS


def mock_get_transactions(
    id_account: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 20,
) -> list[Transaction]:
    """Cain reemplazará el cuerpo por
    `await client.get_account_transactions(id_account, date_from, date_to, limit=limit)`."""
    if id_account != _ACCOUNT_ID_DEMO:
        return []

    items = list(_TRANSACTIONS)
    if date_from:
        items = [t for t in items if t.date >= date_from]
    if date_to:
        items = [t for t in items if t.date <= date_to]
    return items[:limit]


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


def mock_get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
) -> list[ReconciliationMatch]:
    """Consulta el estado de conciliación entre transferencias y
    movimientos. Cain reemplazará el cuerpo por
    `await client.get_reconciliation()`. El seed no trae conciliaciones
    todavía (la transferencia sembrada sigue 'pending')."""
    items = list(_RECONCILIATIONS.values())
    if id_transfer is not None:
        items = [r for r in items if r.id_transfer == id_transfer]
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
