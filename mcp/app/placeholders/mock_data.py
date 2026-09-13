"""
Mocks / placeholders — parte de Guillermo (MCP + modelo de IA).

MIGRACIÓN A LA BASE DE DATOS REAL (Reto-Banorte / BancaAdaptativa.Api):
-------------------------------------------------------------------------
Estos mocks **reflejan el seed rico y determinista de DbSeeder.cs** para el
usuario demo, de modo que la experiencia con API real y sin ella sea la
misma (4 cuentas, 3 tarjetas, 5 metas, presupuestos del mes, etc.):

    Usuario id=1  demo@banorte.mx  "Usuario Demo"  (perfil: discapacidad visual)
    Cuenta id=1  "Nómina"            debito   ****1234  activa
    Cuenta id=2  "Ahorro"            ahorro   ****4321  activa
    Cuenta id=3  "Compras en línea"  debito   ****7788  activa
    Cuenta id=4  "Cuenta antigua"    debito   ****0002  bloqueada
    Transferencias: 6 confirmed + 3 pending + 1 rejected, con conciliación
    Tarjetas: Visa Oro / Mastercard Estándar / Visa Platino Vive+

Regla de oro: cada función mock_* tiene la MISMA firma y el MISMO tipo de
retorno (los modelos de schemas.py) que la llamada real a la API. El día que
todo se atienda con integration/api_client.py, solo cambia el CUERPO de
estas funciones.

Cain puede ubicar rápido qué sigue siendo mock buscando el campo
"x_placeholder": true en cualquier respuesta.
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
        # Derivado de UserProfile.disability_type="visual" (DbSeeder.cs).
        accessibility_profile=AccessibilityProfile.VISUAL_IMPAIRMENT,
    ),
    x_placeholder=True,
)

# ---------------------------------------------------------------------------
# CUENTAS — espejo del seed rico (Nómina primero: id_account 1).
# El saldo de Nómina/Ahorro se recalcula abajo con la serie de balances
# diarios para que cuenta, movimientos y gráfica cuenten la misma historia.
# ---------------------------------------------------------------------------
_ACCOUNTS: list[Account] = [
    Account(
        id_account=1,
        account_type="debito",
        alias="Nómina",
        masked_number="****1234",
        currency="MXN",
        balance=58024.65,
        status="active",
        created_at=_NOW - timedelta(days=90),
        x_placeholder=True,
    ),
    Account(
        id_account=2,
        account_type="ahorro",
        alias="Ahorro",
        masked_number="****4321",
        currency="MXN",
        balance=103036.06,
        status="active",
        created_at=_NOW - timedelta(days=90),
        x_placeholder=True,
    ),
    Account(
        id_account=3,
        account_type="debito",
        alias="Compras en línea",
        masked_number="****7788",
        currency="MXN",
        balance=3617.83,
        status="active",
        created_at=_NOW - timedelta(days=30),
        x_placeholder=True,
    ),
    Account(
        id_account=4,
        account_type="debito",
        alias="Cuenta antigua",
        masked_number="****0002",
        currency="MXN",
        balance=0.0,
        status="closed",  # el schema MCP admite active/frozen/closed (backend: blocked≈closed)
        created_at=_NOW - timedelta(days=700),
        x_placeholder=True,
    ),
]
_ACCOUNT_ID_DEMO = 1

# ---------------------------------------------------------------------------
# TRANSACCIONES por cuenta — vocabulario espejo del ledger de DbSeeder.cs.
# ---------------------------------------------------------------------------
def _tx(i: int, dias: int, monto: float, direction: str, category: str,
        description: str, status: str = "posted", ref: str = "",
        id_expense: Optional[int] = None) -> Transaction:
    return Transaction(
        id_transaction=i,
        date=_HOY - timedelta(days=dias),
        amount=monto,
        direction=direction,
        category=category,
        id_expense_category=id_expense,
        description=description,
        status=status,
        reference=ref or f"SD-{i:04d}",
        x_placeholder=True,
    )


_TRANSACTIONS_BY_ACCOUNT: dict[int, list[Transaction]] = {
    1: [
        _tx(1, 1, 24500.00, "credit", "nomina", "Pago nómina quincenal", ref="NOM-0001"),
        _tx(2, 2, 1450.00, "debit", "super", "Walmart Express", ref="SUP-0002", id_expense=6),
        _tx(3, 2, 185.50, "debit", "transporte", "Uber", ref="UBER-0003", id_expense=7),
        _tx(4, 3, 245.00, "debit", "comida_rapida", "Starbucks Reforma", ref="FAST-0004", id_expense=3),
        _tx(5, 3, 890.75, "debit", "restaurante", "Sushi Roll", ref="REST-0005", id_expense=2),
        _tx(6, 4, 720.00, "debit", "gasolina", "Gasolina Pemex", ref="GAS-0006", id_expense=1),
        _tx(7, 4, 385.20, "debit", "farmacia", "Farmacia Guadalajara", ref="FARM-0007", id_expense=4),
        _tx(8, 5, 229.00, "debit", "suscripcion", "Netflix premium", ref="NFLX-0008", id_expense=8),
        _tx(9, 5, 460.00, "debit", "entretenimiento", "Cinépolis", ref="ENT-0009", id_expense=8),
        _tx(10, 6, 549.00, "debit", "servicios", "Telmex Infinitum", ref="TLMX-0010", id_expense=10),
        _tx(11, 7, 899.00, "debit", "educacion", "Udemy", ref="EDU-0011", id_expense=9),
        _tx(12, 7, 137.50, "debit", "gym", "Gimnasio Smart Fit semanal", ref="GYM-0012"),
        _tx(13, 8, 2000.00, "debit", "transferencia", "Transferencia a Mamá — apoyo mensual", ref="TEXT1"),
        _tx(14, 8, 4500.00, "credit", "freelance", "Proyecto freelance — diseño de interfaz", ref="FRE-0014"),
        _tx(15, 9, 8500.00, "debit", "renta", "Renta departamento", ref="REN-0015"),
        _tx(16, 9, 1300.00, "debit", "pago_tarjeta", "Pago tarjeta Visa Oro ****4021", ref="PTC-15-08"),
        _tx(17, 10, 2000.00, "debit", "pago_tarjeta", "Pago tarjeta Mastercard ****7734", ref="PTC-22-08"),
        _tx(18, 10, 6500.00, "debit", "pago_tarjeta", "Pago tarjeta Visa Platino Vive+ ****1002", ref="PTC-28-08"),
        _tx(19, 10, 3000.00, "debit", "transferencia", "Traspaso a Ahorro — meta mensual", ref="TRA-0019"),
        _tx(20, 12, 3500.00, "debit", "transferencia", "Transferencia a Papá — apoyo mensual", ref="TEXT2"),
        _tx(21, 14, 480.00, "debit", "transferencia", "Traspaso cena — Juan Pablo", ref="TEXT3"),
        _tx(22, 16, 5600.00, "debit", "educacion", "Pago colegiatura ITM", ref="TEXT4", id_expense=9),
        _tx(23, 20, 1800.00, "debit", "transferencia", "Préstamo a Carlos", ref="TEXT5"),
        _tx(24, 25, 650.30, "debit", "medico", "Laboratorio Santa Fe", ref="MED-0024", id_expense=5),
        _tx(25, 1, 380.00, "debit", "entretenimiento", "Cinépolis (en proceso)", status="pending", ref="ENT-0025", id_expense=8),
        _tx(26, 0, 1450.00, "debit", "super", "Walmart Express (en proceso)", status="pending", ref="SUP-0026", id_expense=6),
        _tx(27, 0, 95.00, "credit", "intereses", "Devolución por promoción", status="pending", ref="DEV-0027"),
        _tx(28, 3, 1200.00, "debit", "otro", "Compra declinada por el comercio", status="reversed", ref="FALL-0028"),
        _tx(29, 6, 4500.00, "debit", "transferencia", "Transferencia devuelta — cuenta destino incorrecta", status="reversed", ref="TDEV-0029"),
    ],
    2: [
        _tx(30, 10, 3000.00, "credit", "transferencia", "Traspaso desde Nómina — meta mensual", ref="TRA-0030"),
        _tx(31, 11, 512.40, "credit", "intereses", "Intereses mensuales cuenta ahorro", ref="INT-0031"),
        _tx(32, 18, 850.00, "debit", "otro", "Compra bono verde", ref="AHO-0032"),
    ],
    3: [
        _tx(33, 11, 640.00, "debit", "otro", "Compra en línea Amazon", ref="AMZ-0033"),
        _tx(34, 12, 145.00, "credit", "cashback", "Cashback programa de recompensas", ref="CSH-0034"),
        _tx(35, 5, 1299.00, "debit", "otro", "Compra en línea Mercado Libre", ref="AMZ-0035"),
    ],
    4: [],
}

_TRANSACTIONS: list[Transaction] = [
    t for ts in _TRANSACTIONS_BY_ACCOUNT.values() for t in ts
]

# ---------------------------------------------------------------------------
# BALANCES DIARIOS — serie determinista de 30 días por cuenta activa; el
# saldo final de la serie se escribe de vuelta en Account.balance para que
# cuentas, movimientos y gráfica sean congruentes.
# ---------------------------------------------------------------------------
def _serie_balances(id_cuenta: int, apertura: float, dias: int = 30) -> tuple[list[DailyBalance], float]:
    # Escala de gasto por cuenta: Nómina concentra el gasto diario; Ahorro
    # casi no se toca; Compras en línea tiene actividad moderada.
    escala = {1: 1.0, 2: 0.06, 3: 0.3}.get(id_cuenta, 1.0)
    items: list[DailyBalance] = []
    cierre = round(apertura, 2)
    for i in range(dias - 1, -1, -1):
        d = _HOY - timedelta(days=i)
        income = 0.0
        if id_cuenta == 1 and d.day == 15:
            income = 24500.0
        elif id_cuenta == 2 and d.day == 1:
            income = 512.40
        elif id_cuenta == 2 and d.day == 10:
            income = 3000.00  # traspaso mensual desde Nómina
        elif id_cuenta == 3 and d.day == 18:
            income = 145.00
        base = (d.day * 37 + id_cuenta * 101) % 9
        if d.day % 7 == 0:
            expenses = round((95.50 + base * 60.0) * escala, 2)
        else:
            expenses = round((180.00 + base * 145.75) * escala, 2)
        apertura_dia = cierre
        cierre = round(apertura_dia + income - expenses, 2)
        items.append(DailyBalance(
            id_balance=len(items) + 1,
            date=d,
            opening_balance=apertura_dia,
            income=income,
            expenses=expenses,
            closing_balance=cierre,
            x_placeholder=True,
        ))
    return items, cierre


_DAILY_BALANCES_BY_ACCOUNT: dict[int, list[DailyBalance]] = {}
# Aperturas calculadas para que el cierre de la serie coincida EXACTAMENTE
# con el saldo del snapshot de DbSeeder (58,024.65 / 103,036.06 / 3,617.83).
for _id_cuenta, _apertura in ((1, 54790.40), (2, 100857.19), (3, 10035.12)):
    _serie, _cierre = _serie_balances(_id_cuenta, _apertura)
    _DAILY_BALANCES_BY_ACCOUNT[_id_cuenta] = _serie
    for _c in _ACCOUNTS:
        if _c.id_account == _id_cuenta:
            _c.balance = _cierre

_DAILY_BALANCES: list[DailyBalance] = _DAILY_BALANCES_BY_ACCOUNT[_ACCOUNT_ID_DEMO]

# ---------------------------------------------------------------------------
# TRANSFERENCIAS — espejo del seed: 6 confirmed, 3 pending (simulables),
# 1 rejected. Las dinámicas (prepare/confirm en la demo) se agregan encima.
# ---------------------------------------------------------------------------
def _transfer(i: int, alias: str, masked: str, monto: float, concepto: str,
              status: str, dias: int, origen: int = 1) -> Transfer:
    creada = _NOW - timedelta(days=dias)
    return Transfer(
        id_transfer=i,
        id_origin_account=origen,
        destination_alias=alias,
        destination_masked=masked,
        amount=monto,
        currency="MXN",
        concept=concepto,
        status=status,
        idempotency_key=f"mock-tr-{i:03d}",
        confirmed_at=creada + timedelta(minutes=3) if status == "confirmed" else None,
        x_placeholder=True,
    )


_TRANSFERS: dict[int, Transfer] = {
    t.id_transfer: t
    for t in [
        _transfer(1, "Mamá", "****5678", 2000.0, "Apoyo", TransferStatus.PENDING_CONFIRMATION.value, 0),
        _transfer(2, "Mamá", "****5678", 2000.0, "Apoyo mensual", TransferStatus.CONFIRMED.value, 8),
        _transfer(3, "Papá", "****2210", 3500.0, "Apoyo mensual", TransferStatus.CONFIRMED.value, 12),
        _transfer(4, "Juan Pablo (amigo)", "****8891", 480.0, "Dividir cena", TransferStatus.CONFIRMED.value, 14),
        _transfer(5, "Colegiatura ITM", "****3041", 5600.0, "Pago colegiatura", TransferStatus.CONFIRMED.value, 16),
        _transfer(6, "Carlos (préstamo)", "****6620", 1800.0, "Préstamo personal", TransferStatus.CONFIRMED.value, 20),
        _transfer(7, "Ahorro (propia)", "****4321", 3000.0, "Aporte meta mensual", TransferStatus.CONFIRMED.value, 10),
        _transfer(8, "Luis (hermano)", "****3377", 1500.0, "Regalo de cumpleaños", TransferStatus.PENDING_CONFIRMATION.value, 1),
        _transfer(9, "Ahorro (propia)", "****4321", 2500.0, "Aporte extra meta Viaje a Japón", TransferStatus.PENDING_CONFIRMATION.value, 0),
        _transfer(10, "Cuenta incorrecta", "****9999", 4500.0, "Pago proveedor", "rejected", 6),
    ]
}

# Conciliación: matched (4), pending de revisión (1) y unmatched (1).
_RECONCILIATIONS: dict[int, ReconciliationMatch] = {
    r.id_match: r
    for r in [
        ReconciliationMatch(id_match=1, id_transfer=2, id_transaction=13, status="matched", match_score=0.98, matched_at=_NOW - timedelta(days=8), notes="Conciliación automática por monto y referencia", x_placeholder=True),
        ReconciliationMatch(id_match=2, id_transfer=3, id_transaction=20, status="matched", match_score=0.95, matched_at=_NOW - timedelta(days=12), notes="Conciliación automática por monto y referencia", x_placeholder=True),
        ReconciliationMatch(id_match=3, id_transfer=4, id_transaction=21, status="matched", match_score=0.92, matched_at=_NOW - timedelta(days=14), notes="Conciliación automática por monto y referencia", x_placeholder=True),
        ReconciliationMatch(id_match=4, id_transfer=5, id_transaction=22, status="matched", match_score=0.97, matched_at=_NOW - timedelta(days=16), notes="Conciliación automática por monto y referencia", x_placeholder=True),
        ReconciliationMatch(id_match=5, id_transfer=6, id_transaction=23, status="pending", match_score=0.62, matched_at=None, notes="En revisión manual", x_placeholder=True),
        ReconciliationMatch(id_match=6, id_transfer=10, id_transaction=29, status="mismatch", match_score=0.30, matched_at=None, notes="Transferencia devuelta; sin coincidencia en destino", x_placeholder=True),
    ]
}
_NEXT_TRANSFER_ID = 11

# ---------------------------------------------------------------------------
# CATEGORÍAS DE GASTO — catálogo completo de DbSeeder.cs (10 categorías).
# ---------------------------------------------------------------------------
_EXPENSE_CATEGORIES: list[ExpenseCategory] = [
    ExpenseCategory(id_category=1, name="Gasolina", code="gas", icon="fuel", is_default=True, sort_order=1, x_placeholder=True),
    ExpenseCategory(id_category=2, name="Restaurantes", code="restaurant", icon="restaurant", is_default=True, sort_order=2, x_placeholder=True),
    ExpenseCategory(id_category=3, name="Comida rápida", code="fast_food", icon="fastfood", is_default=True, sort_order=3, x_placeholder=True),
    ExpenseCategory(id_category=4, name="Farmacia", code="drugstore", icon="pharmacy", is_default=True, sort_order=4, x_placeholder=True),
    ExpenseCategory(id_category=5, name="Servicios médicos", code="medical", icon="medical", is_default=True, sort_order=5, x_placeholder=True),
    ExpenseCategory(id_category=6, name="Supermercados", code="supermarket", icon="cart", is_default=True, sort_order=6, x_placeholder=True),
    ExpenseCategory(id_category=7, name="Transporte", code="transport", icon="transport", is_default=True, sort_order=7, x_placeholder=True),
    ExpenseCategory(id_category=8, name="Entretenimiento", code="entertainment", icon="entertainment", is_default=True, sort_order=8, x_placeholder=True),
    ExpenseCategory(id_category=9, name="Educación", code="education", icon="education", is_default=True, sort_order=9, x_placeholder=True),
    ExpenseCategory(id_category=10, name="Servicios básicos", code="utilities", icon="utilities", is_default=True, sort_order=10, x_placeholder=True),
]

# Transaction.category (vocabulario del ledger) -> código del catálogo.
_CATEGORY_TO_CODE = {
    "super": "supermarket",
    "restaurante": "restaurant",
    "comida_rapida": "fast_food",
    "farmacia": "drugstore",
    "medico": "medical",
    "transporte": "transport",
    "gasolina": "gas",
    "entretenimiento": "entertainment",
    "suscripcion": "entertainment",
    "educacion": "education",
    "servicios": "utilities",
}

# ---------------------------------------------------------------------------
# ESTADOS DE CUENTA — 3 meses cerrados de Nómina + 3 de tarjetas (anclados
# a Nómina con cortes 15/22/28, igual que DbSeeder.cs).
# ---------------------------------------------------------------------------
def _fmt_mxn(x: float) -> float:
    return round(x, 2)


_STATEMENTS: dict[int, Statement] = {
    1: Statement(id_statement=1, id_account=1, cut_off_day=30, period_start=date(2026, 6, 1), period_end=date(2026, 6, 30),
                 opening_balance=51200.00, closing_balance=54310.25, total_credits=49000.00, total_debits=45889.75,
                 transaction_count=86, account_type="debito", status="generated", generated_at=_NOW - timedelta(days=72), x_placeholder=True),
    2: Statement(id_statement=2, id_account=1, cut_off_day=31, period_start=date(2026, 7, 1), period_end=date(2026, 7, 31),
                 opening_balance=54310.25, closing_balance=52980.10, total_credits=51200.00, total_debits=52530.15,
                 transaction_count=94, account_type="debito", status="generated", generated_at=_NOW - timedelta(days=42), x_placeholder=True),
    3: Statement(id_statement=3, id_account=1, cut_off_day=31, period_start=date(2026, 8, 1), period_end=date(2026, 8, 31),
                 opening_balance=52980.10, closing_balance=55420.80, total_credits=53500.00, total_debits=51059.30,
                 transaction_count=91, account_type="debito", status="generated", generated_at=_NOW - timedelta(days=11), x_placeholder=True),
    4: Statement(id_statement=4, id_account=1, cut_off_day=15, period_start=date(2026, 7, 16), period_end=date(2026, 8, 15),
                 opening_balance=0.00, closing_balance=11550.40, total_credits=1300.00, total_debits=12850.40,
                 transaction_count=0, account_type="credito", status="generated", generated_at=_NOW - timedelta(days=27), x_placeholder=True),
    5: Statement(id_statement=5, id_account=1, cut_off_day=22, period_start=date(2026, 7, 23), period_end=date(2026, 8, 22),
                 opening_balance=0.00, closing_balance=6420.75, total_credits=2000.00, total_debits=8420.75,
                 transaction_count=0, account_type="credito", status="generated", generated_at=_NOW - timedelta(days=20), x_placeholder=True),
    6: Statement(id_statement=6, id_account=1, cut_off_day=28, period_start=date(2026, 7, 29), period_end=date(2026, 8, 28),
                 opening_balance=0.00, closing_balance=14900.00, total_credits=6500.00, total_debits=21400.00,
                 transaction_count=0, account_type="credito", status="generated", generated_at=_NOW - timedelta(days=14), x_placeholder=True),
}

_STATEMENT_EXPENSES: dict[int, list[StatementExpenseBreakdown]] = {
    3: [
        StatementExpenseBreakdown(id_expense_category=6, category_name="Supermercados", category_code="supermarket", amount=6820.40, transaction_count=12, first_transaction_date=date(2026, 8, 2), last_transaction_date=date(2026, 8, 30)),
        StatementExpenseBreakdown(id_expense_category=2, category_name="Restaurantes", category_code="restaurant", amount=5310.20, transaction_count=9, first_transaction_date=date(2026, 8, 3), last_transaction_date=date(2026, 8, 29)),
        StatementExpenseBreakdown(id_expense_category=7, category_name="Transporte", category_code="transport", amount=2140.75, transaction_count=18, first_transaction_date=date(2026, 8, 1), last_transaction_date=date(2026, 8, 31)),
        StatementExpenseBreakdown(id_expense_category=1, category_name="Gasolina", category_code="gas", amount=2880.00, transaction_count=4, first_transaction_date=date(2026, 8, 5), last_transaction_date=date(2026, 8, 26)),
        StatementExpenseBreakdown(id_expense_category=8, category_name="Entretenimiento", category_code="entertainment", amount=1960.50, transaction_count=7, first_transaction_date=date(2026, 8, 2), last_transaction_date=date(2026, 8, 28)),
        StatementExpenseBreakdown(id_expense_category=10, category_name="Servicios básicos", category_code="utilities", amount=2278.00, transaction_count=5, first_transaction_date=date(2026, 8, 1), last_transaction_date=date(2026, 8, 17)),
    ],
}

# ---------------------------------------------------------------------------
# PRESUPUESTOS — mes de _HOY, espejo del seed (restaurantes rebasado).
# ---------------------------------------------------------------------------
def _budget(i: int, id_cat: int, name: str, code: str, limit: float, spent: float) -> Budget:
    return Budget(
        id_budget=i,
        id_expense_category=id_cat,
        category_name=name,
        category_code=code,
        month=_HOY.month,
        year=_HOY.year,
        amount_limit=limit,
        current_spent=spent,
        usage_percent=_fmt_mxn(spent / limit * 100),
        status="exceeded" if spent >= limit else "active",
        x_placeholder=True,
    )


_BUDGETS: list[Budget] = [
    _budget(1, 2, "Restaurantes", "restaurant", 3200.0, 3980.55),
    _budget(2, 6, "Supermercados", "supermarket", 6000.0, 4120.30),
    _budget(3, 7, "Transporte", "transport", 2400.0, 1580.00),
    _budget(4, 8, "Entretenimiento", "entertainment", 2000.0, 1340.00),
    _budget(5, 10, "Servicios básicos", "utilities", 3000.0, 1975.40),
    _budget(6, 1, "Gasolina", "gas", 2800.0, 2160.00),
]

# ---------------------------------------------------------------------------
# METAS DE AHORRO — espejo del seed (4 activas + 1 completada).
# ---------------------------------------------------------------------------
_SAVINGS_GOALS: list[SavingsGoal] = [
    SavingsGoal(id_goal=1, name="Fondo de emergencia", target_amount=50000.0, current_amount=18750.0, progress_percent=37.50, target_date=_NOW + timedelta(days=180), status="active", created_at=_NOW - timedelta(days=240), updated_at=_NOW - timedelta(days=2), x_placeholder=True),
    SavingsGoal(id_goal=2, name="Viaje a Japón", target_amount=80000.0, current_amount=41200.0, progress_percent=51.50, target_date=_NOW + timedelta(days=300), status="active", created_at=_NOW - timedelta(days=240), updated_at=_NOW - timedelta(days=5), x_placeholder=True),
    SavingsGoal(id_goal=3, name="Enganche del auto", target_amount=350000.0, current_amount=152400.0, progress_percent=43.54, target_date=_NOW + timedelta(days=540), status="active", created_at=_NOW - timedelta(days=240), updated_at=_NOW - timedelta(days=9), x_placeholder=True),
    SavingsGoal(id_goal=4, name="Laptop nueva", target_amount=28000.0, current_amount=24600.0, progress_percent=87.86, target_date=_NOW + timedelta(days=60), status="active", created_at=_NOW - timedelta(days=240), updated_at=_NOW - timedelta(days=1), x_placeholder=True),
    SavingsGoal(id_goal=5, name="Bici eléctrica", target_amount=15000.0, current_amount=15000.0, progress_percent=100.0, target_date=_NOW - timedelta(days=30), status="completed", created_at=_NOW - timedelta(days=240), updated_at=_NOW - timedelta(days=30), x_placeholder=True),
]

# ---------------------------------------------------------------------------
# TARJETAS DE CRÉDITO — espejo del seed (3 tarjetas) + su statement del mes
# anterior (cortes 15/22/28 anclados a Nómina, ids 4/5/6 de _STATEMENTS).
# ---------------------------------------------------------------------------
_CREDIT_CARDS: list[CreditCard] = [
    CreditCard(id_credit_card=1, card_number_masked="****4021", card_type="Visa Oro", credit_limit=50000.0, available_credit=38449.60, interest_rate=3.2, statement_cut_off_day=15, payment_due_day=5, status="active", created_at=_NOW - timedelta(days=420), x_placeholder=True),
    CreditCard(id_credit_card=2, card_number_masked="****7734", card_type="Mastercard Estándar", credit_limit=30000.0, available_credit=23579.25, interest_rate=3.8, statement_cut_off_day=22, payment_due_day=12, status="active", created_at=_NOW - timedelta(days=420), x_placeholder=True),
    CreditCard(id_credit_card=3, card_number_masked="****1002", card_type="Visa Platino Vive+", credit_limit=120000.0, available_credit=105100.0, interest_rate=2.4, statement_cut_off_day=28, payment_due_day=8, status="active", created_at=_NOW - timedelta(days=420), x_placeholder=True),
]

_CREDIT_CARD_STATEMENTS: dict[int, list[CreditCardStatement]] = {
    1: [CreditCardStatement(id_credit_card_statement=1, id_credit_card=1, id_statement=4, period_start=date(2026, 7, 16), period_end=date(2026, 8, 15), previous_balance=0.0, total_payments=1300.0, total_credits=1300.0, total_purchases=12850.40, interest_charges=0.0, minimum_payment=577.52, payment_due_date=date(2026, 8, 5), available_credit=38449.60, status="generated", generated_at=_NOW - timedelta(days=27), x_placeholder=True)],
    2: [CreditCardStatement(id_credit_card_statement=2, id_credit_card=2, id_statement=5, period_start=date(2026, 7, 23), period_end=date(2026, 8, 22), previous_balance=0.0, total_payments=2000.0, total_credits=2000.0, total_purchases=8420.75, interest_charges=0.0, minimum_payment=321.04, payment_due_date=date(2026, 8, 12), available_credit=23579.25, status="generated", generated_at=_NOW - timedelta(days=20), x_placeholder=True)],
    3: [CreditCardStatement(id_credit_card_statement=3, id_credit_card=3, id_statement=6, period_start=date(2026, 7, 29), period_end=date(2026, 8, 28), previous_balance=0.0, total_payments=6500.0, total_credits=6500.0, total_purchases=21400.0, interest_charges=0.0, minimum_payment=745.0, payment_due_date=date(2026, 8, 8), available_credit=105100.0, status="generated", generated_at=_NOW - timedelta(days=14), x_placeholder=True)],
}


# ---------------------------------------------------------------------------
# Funciones mock — misma firma/retorno que las llamadas reales.
# ---------------------------------------------------------------------------
def mock_get_user_context(id_user: int) -> Optional[UserContext]:
    """Devuelve el usuario semilla si id_user coincide (o si no se sabe
    cuál es, se sigue devolviendo el único usuario demo)."""
    if id_user not in (None, _USER_DEMO.id_user):
        return None
    return _USER_DEMO


def mock_get_accounts(
    id_user: int,
    status: Optional[str] = None,
    account_type: Optional[str] = None,
) -> list[Account]:
    """Espejo de GET /accounts (con filtros ?status & ?accountType)."""
    items = list(_ACCOUNTS)
    if status:
        items = [a for a in items if a.status == status]
    if account_type:
        items = [a for a in items if a.account_type == account_type]
    return items


def mock_get_account_summary(id_user: int) -> AccountSummary:
    """Espejo de GET /me/account-summary: total = suma de las 4 cuentas."""
    cuentas = _ACCOUNTS
    total = sum(a.balance for a in cuentas)
    moneda = cuentas[0].currency if cuentas else "MXN"
    return AccountSummary(total_balance=round(total, 2), currency=moneda, accounts=cuentas, x_placeholder=True)


def mock_get_account_detail(id_account: int) -> Optional[Account]:
    """Espejo de GET /accounts/{accountId}."""
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
    """Espejo de GET /accounts/{accountId}/transactions."""
    items = _TRANSACTIONS_BY_ACCOUNT.get(id_account, [])
    return _filtrar_transacciones(
        items, date_from, date_to, category, expense_category, direction, status, search
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
    """Espejo de GET /me/transactions (movimientos de TODAS las cuentas)."""
    if id_account is not None:
        items = _TRANSACTIONS_BY_ACCOUNT.get(id_account, [])
    else:
        items = sorted(_TRANSACTIONS, key=lambda t: t.date, reverse=True)
    return _filtrar_transacciones(
        items, date_from, date_to, category, expense_category, direction, status, search
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
        resultado = [
            t for t in resultado
            if t.category == expense_category or _CATEGORY_TO_CODE.get(t.category) == expense_category
        ]
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
    """Espejo de GET /accounts/{accountId}/daily-balances (serie de 30 días)."""
    items = list(_DAILY_BALANCES_BY_ACCOUNT.get(id_account, []))
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
    """Placeholder de /memory/query (el backend aún no expone el endpoint)."""
    return []


def mock_prepare_transfer(
    id_user: int,
    id_origin_account: int,
    destination_alias: str,
    amount: float,
    currency: str = "MXN",
    concept: str = "",
) -> Transfer:
    """Crea un BORRADOR de transferencia (aún no confirmado)."""
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
    """Confirma una transferencia previamente creada."""
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
    """Espejo de GET /transfers (historial)."""
    items = list(_TRANSFERS.values())
    if status:
        items = [t for t in items if t.status == status]
    if id_origin_account is not None:
        items = [t for t in items if t.id_origin_account == id_origin_account]
    return items[:limit]


def mock_get_transfer_detail(id_transfer: int) -> Optional[Transfer]:
    """Espejo de GET /transfers/{transferId}."""
    return _TRANSFERS.get(id_transfer)


def mock_get_reconciliation_status(
    id_user: Optional[int] = None,
    id_transfer: Optional[int] = None,
    id_account: Optional[int] = None,
    status: Optional[str] = None,
) -> list[ReconciliationMatch]:
    """Espejo de GET /reconciliation: matched/pending/unmatched del seed."""
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
    """Espejo de GET /accounts/{accountId}/statements."""
    items = [s for s in _STATEMENTS.values() if s.id_account == id_account]
    if year is not None:
        items = [s for s in items if s.period_start.year == year]
    if month is not None:
        items = [s for s in items if s.period_start.month == month]
    if status:
        items = [s for s in items if s.status == status]
    return sorted(items, key=lambda s: s.period_end, reverse=True)


def mock_get_statement_detail(id_account: int, id_statement: int) -> Optional[StatementDetail]:
    """Espejo de GET /accounts/{accountId}/statements/{statementId}."""
    statement = _STATEMENTS.get(id_statement)
    if statement is None or statement.id_account != id_account:
        return None
    return StatementDetail(statement=statement, expenses=_STATEMENT_EXPENSES.get(id_statement, []))


def mock_get_expense_categories(search: Optional[str] = None) -> list[ExpenseCategory]:
    """Espejo de GET /expense-categories ENRIQUECIDO con el gasto real
    (suma y conteo de movimientos débito) agregado por categoría del
    catálogo (mapeando el vocabulario del ledger a códigos)."""
    gasto_por_codigo: dict[str, tuple[float, int]] = {}
    for t in _TRANSACTIONS:
        if t.direction != "debit" or t.status == "failed":
            continue
        codigo = _CATEGORY_TO_CODE.get(t.category)
        if codigo is None:
            continue
        monto, conteo = gasto_por_codigo.get(codigo, (0.0, 0))
        gasto_por_codigo[codigo] = (monto + t.amount, conteo + 1)

    items = [
        c.model_copy(
            update={
                "total_amount": _fmt_mxn(gasto_por_codigo.get(c.code, (0.0, 0))[0]),
                "transaction_count": gasto_por_codigo.get(c.code, (0.0, 0))[1],
            }
        )
        for c in _EXPENSE_CATEGORIES
    ]
    if search:
        texto = search.lower()
        items = [c for c in items if texto in c.name.lower() or texto in c.code.lower()]
    return sorted(items, key=lambda c: c.total_amount, reverse=True)


def mock_get_budgets_monthly(
    year: int,
    month: int,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> BudgetMonthlySummary:
    """Espejo de GET /me/budgets/monthly."""
    items = [b for b in _BUDGETS if b.year == year and b.month == month]
    if category:
        items = [b for b in items if b.category_code == category]
    if status:
        items = [b for b in items if b.status == status]
    total_limit = sum(b.amount_limit for b in items)
    total_spent = sum(b.current_spent for b in items)
    return BudgetMonthlySummary(month=month, year=year, total_limit=_fmt_mxn(total_limit), total_spent=_fmt_mxn(total_spent), budgets=items)


def mock_get_savings_goals(status: Optional[str] = None) -> list[SavingsGoal]:
    """Espejo de GET /me/savings-goals."""
    items = list(_SAVINGS_GOALS)
    if status:
        items = [g for g in items if g.status == status]
    return items


def mock_get_credit_cards(status: Optional[str] = None) -> list[CreditCard]:
    """Espejo de GET /me/credit-cards."""
    items = list(_CREDIT_CARDS)
    if status:
        items = [c for c in items if c.status == status]
    return items


def mock_get_credit_card_statements(
    id_credit_card: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> list[CreditCardStatement]:
    """Espejo de GET /me/credit-cards/{cardId}/statements."""
    items = _CREDIT_CARD_STATEMENTS.get(id_credit_card, [])
    if year is not None:
        items = [s for s in items if s.period_end.year == year]
    if month is not None:
        items = [s for s in items if s.period_end.month == month]
    return items


# ---------------------------------------------------------------------------
# UTILIDAD PARA CAIN: ubicar qué respuestas siguen siendo datos de demo
# ---------------------------------------------------------------------------
def find_placeholders(data) -> list[str]:
    """Devuelve las 'rutas' de todos los objetos marcados con
    'x_placeholder': true dentro de una estructura (dicts/lists)."""
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
