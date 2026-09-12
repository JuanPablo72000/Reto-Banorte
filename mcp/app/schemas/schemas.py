""""
Schemas compartidos — parte de Guillermo (MCP + modelo de IA).

MIGRACIÓN A LA BASE DE DATOS REAL (Reto-Banorte / BancaAdaptativa.Api):
-------------------------------------------------------------------------
Antes estos modelos usaban IDs de texto inventados (p.ej. "acc_123",
"user_1") porque no existía backend real. Ahora sí existe
(backend/src/BancaAdaptativa.Api de Pablo), y define:

  - PKs enteras autoincrementales: IdUser, IdAccount, IdTransaction,
    IdTransfer, IdBalance, IdMatch, IdConfirmation, IdPreference...
  - JSON en camelCase (Program.cs: JsonNamingPolicy.CamelCase), p.ej.
    {"idAccount": 1, "accountType": "debito", ...}
  - Fechas de solo-día (DateOnly) para transacciones/balances, y
    datetime completo (UTC) para timestamps.

Por eso cada entidad de este archivo:
  1. Usa nombres de campo en snake_case estilo Python (id_account,
     account_type...) pero con un alias_generator a camelCase, así que
     Cain puede hacer `Account.model_validate(json_de_la_api)` directo,
     sin transformar nada.
  2. Usa `int` para todos los IDs (antes eran `str` con placeholders de
     texto tipo "__PLACEHOLDER_ACCOUNT_ID__").

Todo lo que NO viene de la API real (metadata visual/accesibilidad,
"x_position", etc.) se queda igual: es una capa nuestra para la UI futura,
no del backend de Pablo.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.ia.accessibility_templates import ACCESSIBILITY_TEMPLATE_IDS


class ApiModel(BaseModel):
    """Base para cualquier modelo que pueda poblarse directo desde el JSON
    (camelCase) de BancaAdaptativa.Api. `populate_by_name=True` permite
    seguir construyendo estos modelos con kwargs en snake_case (como hacen
    los placeholders/mocks) sin tener que escribir el alias a mano."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------------------
# Nombres de tools MCP
#
# Ampliado para reflejar los endpoints NUEVOS que Pablo agregó a
# BancaAdaptativa.Api (estados de cuenta, presupuestos, metas de ahorro,
# tarjetas de crédito, categorías de gasto, listado global de movimientos y
# de transferencias). Todas son de SOLO LECTURA salvo prepare_transfer/
# confirm_transfer: el catálogo IA de Pablo (docs/datos/06-catalogo-ia-
# placeholders.md, sección 6.5) es explícito en que la IA "no escribe" salvo
# confirmar una transferencia ya creada — crear presupuestos/tarjetas/metas
# lo hace el usuario desde la UI, no la IA. Por eso NO hay
# create_budget/pay_credit_card/etc. aquí, aunque esos endpoints POST/PUT/
# DELETE sí existan en la API real.
# ---------------------------------------------------------------------------
TOOL_NAMES = [
    "get_user_context",
    "get_accounts",
    "get_account_summary",
    "get_account_detail",
    "get_transactions",
    "get_all_transactions",
    "get_daily_balance",
    "search_memory_context",
    "prepare_transfer",
    "confirm_transfer",
    "get_transfers",
    "get_transfer_detail",
    "get_reconciliation_status",
    "get_statements",
    "get_statement_detail",
    "get_expense_categories",
    "get_budgets_monthly",
    "get_savings_goals",
    "get_credit_cards",
    "get_credit_card_statements",
]

ToolName = Literal[
    "get_user_context",
    "get_accounts",
    "get_account_summary",
    "get_account_detail",
    "get_transactions",
    "get_all_transactions",
    "get_daily_balance",
    "search_memory_context",
    "prepare_transfer",
    "confirm_transfer",
    "get_transfers",
    "get_transfer_detail",
    "get_reconciliation_status",
    "get_statements",
    "get_statement_detail",
    "get_expense_categories",
    "get_budgets_monthly",
    "get_savings_goals",
    "get_credit_cards",
    "get_credit_card_statements",
]


class UIHint(str, Enum):
    FORM = "form"
    CONFIRMATION = "confirmation"
    TABLE = "table"
    SUMMARY = "summary"
    NONE = "none"
    ALERT = "alert"
    TUTORIAL = "tutorial"
    SUGGESTION = "suggestion"


class Section(str, Enum):
    HEADER = "header"
    MAIN = "main"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    MODAL = "modal"
    INLINE = "inline"
    NOTIFICATION = "notification"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


class AccessibilityProfile(str, Enum):
    DEFAULT = "default"
    SENIOR = "senior"
    VISUAL_IMPAIRMENT = "visual_impairment"
    MOTOR_IMPAIRMENT = "motor_impairment"
    COGNITIVE_IMPAIRMENT = "cognitive_impairment"
    LOW_LITERACY = "low_literacy"


class IconType(str, Enum):
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    TRANSFER = "transfer"
    BALANCE = "balance"
    SEARCH = "search"
    HELP = "help"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"
    SETTINGS = "settings"
    # Añadidos junto con los nuevos endpoints de Pablo (estados de cuenta,
    # presupuestos, metas de ahorro, tarjetas de crédito, categorías).
    STATEMENT = "statement"
    BUDGET = "budget"
    GOAL = "goal"
    CARD = "card"
    CATEGORY = "category"


class ComponentVariant(str, Enum):
    """Valores EXACTOS del prop `variant` de Button/IconButton en
    frontend/src/components/ui — la IA elige uno de estos 4, nunca un
    color hex o una clase de Tailwind suelta."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    GHOST = "ghost"
    DANGER = "danger"


class BadgeTone(str, Enum):
    """Valores EXACTOS del tono de Badge/Tag en frontend/src/components/ui
    (los 5 estados del preview: Confirmada, Pendiente, Fallida, En
    revisión, Borrador)."""
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"
    NEUTRAL = "neutral"


class VisualMetadata(BaseModel):
    """Metadata visual enriquecida para la UI (no viene del backend).

    "variant" y "tone" son catálogos CERRADOS que calzan 1:1 con los props
    reales de los componentes de Juan Pablo (Button, IconButton, Badge,
    Tag): la IA solo elige un valor de estas listas, nunca decide colores,
    clases de Tailwind ni tamaños. El tamaño (sm/md/lg) y el
    espaciado/orden final los resuelve SIEMPRE la plantilla de
    accesibilidad (app/ia/accessibility_templates.py) + PositionMetadata
    de abajo — nunca la IA por elemento — para que el frontend arme la
    pantalla de forma automática y consistente."""
    icon: IconType = Field(
        default=IconType.INFO,
        description="Icono lógico (el frontend lo mapea a un ReactNode fijo, la IA nunca manda JSX/SVG)"
    )
    variant: ComponentVariant = Field(
        default=ComponentVariant.PRIMARY,
        description="Variant EXACTO de Button/IconButton: primary, secondary, ghost o danger"
    )
    tone: Optional[BadgeTone] = Field(
        default=None,
        description="Tono EXACTO de Badge/Tag cuando el elemento se renderiza como uno; null si no aplica"
    )
    emphasis: Literal["normal", "highlighted", "subtle"] = Field(default="normal")
    animation: Literal["none", "fade", "slide", "pulse"] = Field(
        default="none",
        description="Tipo de animación (none si reduced_motion está activo)"
    )


class AccessibilityMetadata(BaseModel):
    """Metadata de accesibilidad por elemento (no viene del backend)."""
    aria_label: str = Field(description="Etiqueta ARIA para lectores de pantalla")
    screen_reader_text: str = Field(description="Texto completo para lectores de pantalla")
    focusable: bool = Field(default=True)
    keyboard_shortcut: Optional[str] = Field(default=None)
    plain_language_text: Optional[str] = Field(
        default=None,
        description="Versión en lenguaje simple del texto"
    )
    tooltip: Optional[str] = Field(default=None)
    senior_adaptations: Optional[dict] = Field(
        default=None,
        description="Adaptaciones para adultos mayores: font_scale, button_size, etc."
    )
    visual_impairment_adaptations: Optional[dict] = Field(
        default=None,
        description="Adaptaciones para discapacidad visual: high_contrast, audio_cue, etc."
    )


class PositionMetadata(BaseModel):
    """Metadatos de posicionamiento con información visual y de accesibilidad."""
    display_order: int = Field(default=1)
    section: Section = Field(default=Section.MAIN)
    priority: Priority = Field(default=Priority.MEDIUM)
    visual: VisualMetadata = Field(default_factory=VisualMetadata)
    accessibility: AccessibilityMetadata


class SuggestedAction(BaseModel):
    """Acción sugerida relacionada con el paso actual. Se renderiza SIEMPRE
    como un botón (Button/IconButton) en el frontend."""
    action_id: str = Field(description="ID único de la sugerencia")
    label: str = Field(description="Texto del botón/enlace")
    description: str = Field(description="Descripción breve de qué hace")
    tool: ToolName = Field(description="Tool MCP a invocar")
    arguments: dict = Field(default_factory=dict)
    ui_hint: UIHint = Field(default=UIHint.SUGGESTION)
    reason: str = Field(description="Por qué sugerimos esta acción")
    icon: IconType = Field(default=IconType.INFO)
    variant: ComponentVariant = Field(
        default=ComponentVariant.SECONDARY,
        description="Variant del botón: primary solo para LA sugerencia más relevante, danger solo para acciones destructivas, secondary/ghost para el resto"
    )
    priority: Priority = Field(default=Priority.LOW)


# ---------------------------------------------------------------------------
# ENTIDADES — alineadas 1:1 con los DTOs reales de BancaAdaptativa.Api
# (backend/src/BancaAdaptativa.Api/Dtos/**). Los campos "x_placeholder" y
# "x_position" son nuestros, no del backend: marcan si el dato mostrado es
# un placeholder de demo y cómo debe posicionarse/leerse en la UI.
# ---------------------------------------------------------------------------
class AccessibilityPreference(ApiModel):
    """Espejo de Dtos/Preferences/AccessibilityPreferenceResponse."""
    id_preference: int
    font_scale: float = Field(1.0)
    high_contrast: bool = False
    dark_mode: bool = False
    reduced_motion: bool = False
    large_targets: bool = False
    plain_language: bool = False
    updated_at: datetime
    # No viene de la API: lo derivamos nosotros (senior/visual_impairment/...)
    # a partir de UserProfile.disability_type + estas preferencias, para
    # elegir qué bloque de "messages" mostrar en el ActionPlan.
    accessibility_profile: AccessibilityProfile = Field(default=AccessibilityProfile.DEFAULT)


class UserContext(ApiModel):
    """Combina Dtos/Auth/UserDto + Dtos/Preferences/AccessibilityPreferenceResponse
    (equivale a GET /users/me + GET /me/preferences, ver mcp_server.py)."""
    id_user: int
    name: str
    email: str
    locale: str = "es-MX"
    status: Literal["active", "blocked", "pending"] = "active"
    accessibility: AccessibilityPreference
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.HEADER,
            priority=Priority.HIGH,
            visual=VisualMetadata(icon=IconType.ACCOUNT, variant=ComponentVariant.PRIMARY),
            accessibility=AccessibilityMetadata(
                aria_label="Información del usuario",
                screen_reader_text="Perfil del usuario autenticado",
                plain_language_text="Tu información personal",
                tooltip="Ver y editar tu perfil"
            )
        )
    )


class Account(ApiModel):
    """Espejo de Dtos/Accounts/AccountResponse."""
    id_account: int
    # str y no Literal: el seed real (DbSeeder.cs) usa "debito"/"credito" en
    # español, no los valores en inglés que se habían inventado antes.
    account_type: str
    alias: str
    masked_number: str
    currency: str = "MXN"
    balance: float
    status: Literal["active", "frozen", "closed"] = "active"
    created_at: datetime
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.HIGH,
            visual=VisualMetadata(
                icon=IconType.ACCOUNT,
                variant=ComponentVariant.PRIMARY,
                emphasis="highlighted"
            ),
            accessibility=AccessibilityMetadata(
                aria_label="Cuenta bancaria",
                screen_reader_text="Cuenta bancaria con saldo disponible",
                plain_language_text="Tu cuenta de dinero",
                tooltip="Ver detalles de la cuenta",
                keyboard_shortcut="Alt+C",
                senior_adaptations={
                    "font_scale": 1.5,
                    "button_size": "lg",
                    "show_balance_prominent": True
                }
            )
        )
    )


class Transaction(ApiModel):
    """Espejo de Dtos/Transactions/TransactionResponse."""
    id_transaction: int
    date: date
    amount: float
    direction: Literal["credit", "debit"]
    category: str
    description: str
    status: Literal["posted", "pending", "reversed"] = "posted"
    reference: Optional[str] = None
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(
                icon=IconType.TRANSACTION,
                variant=ComponentVariant.SECONDARY,
                tone=BadgeTone.INFO,
                animation="fade"
            ),
            accessibility=AccessibilityMetadata(
                aria_label="Transacción",
                screen_reader_text="Movimiento de la cuenta",
                plain_language_text="Dinero que entró o salió",
                tooltip="Ver detalles del movimiento"
            )
        )
    )


class DailyBalance(ApiModel):
    """Espejo de Dtos/Transactions/DailyBalanceResponse."""
    id_balance: int
    date: date
    opening_balance: float
    income: float
    expenses: float
    closing_balance: float
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(
                icon=IconType.BALANCE,
                variant=ComponentVariant.SECONDARY,
                tone=BadgeTone.SUCCESS,
                emphasis="highlighted"
            ),
            accessibility=AccessibilityMetadata(
                aria_label="Balance diario",
                screen_reader_text="Resumen del balance del día",
                plain_language_text="Cuánto dinero tienes hoy",
                tooltip="Ver tu balance del día"
            )
        )
    )


class TransferStatus(str, Enum):
    PENDING = "pending"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Transfer(ApiModel):
    """Espejo de Dtos/Transfers/TransferResponse."""
    id_transfer: int
    id_origin_account: int
    destination_alias: str
    destination_masked: str
    amount: float
    currency: str = "MXN"
    concept: str = ""
    status: str = "pending"
    idempotency_key: str
    confirmed_at: Optional[datetime] = None
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MODAL,
            priority=Priority.HIGH,
            visual=VisualMetadata(
                icon=IconType.TRANSFER,
                variant=ComponentVariant.PRIMARY,
                tone=BadgeTone.WARNING,
                emphasis="highlighted",
                animation="slide"
            ),
            accessibility=AccessibilityMetadata(
                aria_label="Transferencia",
                screen_reader_text="Información de la transferencia",
                plain_language_text="Enviar dinero a otra persona",
                tooltip="Revisar y confirmar la transferencia",
                keyboard_shortcut="Alt+T"
            )
        )
    )


class TransferConfirmation(ApiModel):
    """Espejo de Dtos/Transfers/TransferConfirmationResponse. El backend
    real devuelve esto junto al Transfer al confirmar
    (POST /transfers/{id}/confirm -> {"transfer": ..., "confirmation": ...})."""
    id_confirmation: int
    method: str
    status: str
    confirmed_at: Optional[datetime] = None


class ReconciliationMatch(ApiModel):
    """Espejo de Dtos/Reconciliation/ReconciliationResponse."""
    id_match: int
    id_transfer: int
    id_transaction: int
    status: Literal["matched", "pending", "mismatch"] = "pending"
    match_score: float = Field(ge=0.0, le=1.0, default=0.0)
    matched_at: Optional[datetime] = None
    notes: str = ""
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(icon=IconType.SUCCESS, variant=ComponentVariant.SECONDARY, tone=BadgeTone.SUCCESS),
            accessibility=AccessibilityMetadata(
                aria_label="Conciliación",
                screen_reader_text="Estado de conciliación de la transferencia",
                plain_language_text="Verificar que el envío se hizo correctamente"
            )
        )
    )


class AccountSummary(ApiModel):
    """Espejo de Dtos/Accounts/AccountSummaryResponse
    (GET /me/account-summary): saldo total + desglose por cuenta."""
    total_balance: float
    currency: str = "MXN"
    accounts: list[Account] = Field(default_factory=list)
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.HEADER,
            priority=Priority.HIGH,
            visual=VisualMetadata(icon=IconType.BALANCE, variant=ComponentVariant.PRIMARY, emphasis="highlighted"),
            accessibility=AccessibilityMetadata(
                aria_label="Saldo total",
                screen_reader_text="Saldo total de todas tus cuentas",
                plain_language_text="Todo tu dinero junto",
                tooltip="Ver el desglose por cuenta"
            )
        )
    )


class ExpenseCategory(ApiModel):
    """Espejo de Dtos/Common/CommonDtos.cs -> ExpenseCategoryResponse
    (GET /expense-categories)."""
    id_category: int
    name: str
    code: str
    icon: Optional[str] = None
    is_default: bool = False
    sort_order: int = 0
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.SIDEBAR,
            priority=Priority.LOW,
            visual=VisualMetadata(icon=IconType.CATEGORY, variant=ComponentVariant.GHOST),
            accessibility=AccessibilityMetadata(
                aria_label="Categoría de gasto",
                screen_reader_text="Categoría usada para clasificar gastos",
                plain_language_text="Tipo de gasto",
                tooltip="Filtrar por esta categoría"
            )
        )
    )


class StatementExpenseBreakdown(ApiModel):
    """Espejo de Dtos/Accounts/StatementDtos.cs -> StatementExpenseBreakdown
    (parte de GET /accounts/{accountId}/statements/{statementId})."""
    id_expense_category: int
    category_name: str
    category_code: str
    amount: float
    transaction_count: int = 0
    first_transaction_date: Optional[date] = None
    last_transaction_date: Optional[date] = None


class Statement(ApiModel):
    """Espejo de Dtos/Accounts/StatementDtos.cs -> StatementResponse
    (GET /accounts/{accountId}/statements)."""
    id_statement: int
    id_account: int
    cut_off_day: int
    period_start: date
    period_end: date
    opening_balance: float
    closing_balance: float
    total_credits: float
    total_debits: float
    transaction_count: int = 0
    account_type: Optional[str] = None
    status: Literal["generated", "archived"] = "generated"
    generated_at: datetime
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(icon=IconType.STATEMENT, variant=ComponentVariant.SECONDARY, tone=BadgeTone.INFO),
            accessibility=AccessibilityMetadata(
                aria_label="Estado de cuenta",
                screen_reader_text="Estado de cuenta de un periodo",
                plain_language_text="Resumen de un mes de tu cuenta",
                tooltip="Ver el detalle de este estado de cuenta"
            )
        )
    )


class StatementDetail(ApiModel):
    """Espejo de Dtos/Accounts/StatementDtos.cs -> StatementDetailResponse
    (GET /accounts/{accountId}/statements/{statementId}): el estado de
    cuenta + su desglose de gastos por categoría."""
    statement: Statement
    expenses: list[StatementExpenseBreakdown] = Field(default_factory=list)


class Budget(ApiModel):
    """Espejo de Dtos/Budgets/BudgetDtos.cs -> BudgetResponse."""
    id_budget: int
    id_expense_category: int
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    month: int
    year: int
    amount_limit: float
    current_spent: float = 0.0
    usage_percent: float = 0.0
    status: Literal["active", "exceeded"] = "active"
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(icon=IconType.BUDGET, variant=ComponentVariant.SECONDARY, tone=BadgeTone.WARNING),
            accessibility=AccessibilityMetadata(
                aria_label="Presupuesto",
                screen_reader_text="Presupuesto mensual de una categoría de gasto",
                plain_language_text="Cuánto puedes gastar en esto este mes",
                tooltip="Ver el detalle de este presupuesto"
            )
        )
    )


class BudgetMonthlySummary(ApiModel):
    """Espejo de Dtos/Budgets/BudgetDtos.cs -> BudgetMonthlySummaryResponse
    (GET /me/budgets/monthly)."""
    month: int
    year: int
    total_limit: float = 0.0
    total_spent: float = 0.0
    budgets: list[Budget] = Field(default_factory=list)


class SavingsGoal(ApiModel):
    """Espejo de Dtos/SavingsGoals/SavingsGoalDtos.cs -> SavingsGoalResponse
    (GET /me/savings-goals)."""
    id_goal: int
    name: str
    target_amount: float
    current_amount: float = 0.0
    progress_percent: float = 0.0
    target_date: datetime
    status: Literal["active", "paused", "completed"] = "active"
    created_at: datetime
    updated_at: datetime
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(icon=IconType.GOAL, variant=ComponentVariant.SECONDARY, tone=BadgeTone.SUCCESS, emphasis="highlighted"),
            accessibility=AccessibilityMetadata(
                aria_label="Meta de ahorro",
                screen_reader_text="Meta de ahorro con su avance",
                plain_language_text="Cuánto llevas ahorrado para esto",
                tooltip="Ver el detalle de esta meta"
            )
        )
    )


class CreditCard(ApiModel):
    """Espejo de Dtos/Accounts/CreditCardDtos.cs -> CreditCardResponse
    (GET/POST /me/credit-cards)."""
    id_credit_card: int
    card_number_masked: str
    card_type: Optional[str] = None
    credit_limit: float
    available_credit: float
    interest_rate: float = 0.0
    statement_cut_off_day: int
    payment_due_day: int
    status: Literal["active", "blocked", "cancelled"] = "active"
    created_at: datetime
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.HIGH,
            visual=VisualMetadata(icon=IconType.CARD, variant=ComponentVariant.PRIMARY, emphasis="highlighted"),
            accessibility=AccessibilityMetadata(
                aria_label="Tarjeta de crédito",
                screen_reader_text="Tarjeta de crédito con su límite y crédito disponible",
                plain_language_text="Tu tarjeta de crédito",
                tooltip="Ver los estados de cuenta de esta tarjeta"
            )
        )
    )


class CreditCardStatement(ApiModel):
    """Espejo de Dtos/Accounts/CreditCardDtos.cs -> CreditCardStatementResponse
    (GET /me/credit-cards/{cardId}/statements)."""
    id_credit_card_statement: int
    id_credit_card: int
    id_statement: int
    period_start: date
    period_end: date
    previous_balance: float = 0.0
    total_payments: float = 0.0
    total_credits: float = 0.0
    total_purchases: float = 0.0
    interest_charges: float = 0.0
    minimum_payment: float = 0.0
    payment_due_date: date
    available_credit: float = 0.0
    status: Literal["generated", "archived"] = "generated"
    generated_at: datetime
    x_placeholder: bool = Field(default=False)
    x_position: PositionMetadata = Field(
        default_factory=lambda: PositionMetadata(
            display_order=1,
            section=Section.MAIN,
            priority=Priority.MEDIUM,
            visual=VisualMetadata(icon=IconType.STATEMENT, variant=ComponentVariant.SECONDARY, tone=BadgeTone.INFO),
            accessibility=AccessibilityMetadata(
                aria_label="Estado de cuenta de tarjeta",
                screen_reader_text="Estado de cuenta de la tarjeta de crédito",
                plain_language_text="Resumen de un mes de tu tarjeta",
                tooltip="Ver el mínimo a pagar y la fecha límite"
            )
        )
    )


class MemoryEvent(ApiModel):
    """Espejo de Models/MemoryEvent.cs. Pablo TODAVÍA no expone un endpoint
    /memory/query en la API real (no está en Endpoints/*), así que
    search_memory_context sigue siendo mock (ver placeholders/mock_data.py)
    hasta que ese endpoint exista. Se deja tipado ya con IDs reales para
    que el cambio, cuando llegue, sea solo de mock_data.py."""
    id_event: int
    id_session: int
    id_user: int
    id_detected_preference: Optional[int] = None
    event_type: str
    intent: str
    target_element: str = ""
    redacted_summary: str
    sensitivity_level: Literal["low", "medium", "high"] = "low"
    created_at: datetime
    retention_until: Optional[datetime] = None
    x_placeholder: bool = Field(default=False)


class AuditLog(ApiModel):
    """Espejo de Models/AuditLog.cs. Igual que MemoryEvent: no hay endpoint
    /audit/me todavía en Endpoints/*, se deja tipado para cuando exista."""
    id_log: int
    id_user: int
    action: str
    resource: str
    result: Literal["success", "failure", "denied"] = "success"
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    redacted_payload: str = ""
    created_at: datetime
    x_placeholder: bool = Field(default=False)


# ---------------------------------------------------------------------------
# ARGUMENTOS DE ENTRADA por tool — IDs ahora `int` (antes `str`), igual que
# las PKs reales (IdUser, IdAccount, IdTransfer...) de BancaAdaptativa.Api.
# ---------------------------------------------------------------------------
class GetUserContextArgs(BaseModel):
    id_user: int


class GetAccountsArgs(BaseModel):
    id_user: int


class GetTransactionsArgs(BaseModel):
    id_account: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: int = Field(20, ge=1, le=200)


class GetDailyBalanceArgs(BaseModel):
    id_account: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class SearchMemoryContextArgs(BaseModel):
    id_user: int
    id_session: Optional[int] = None
    query: str
    limit: int = Field(10, ge=1, le=50)


class PrepareTransferArgs(BaseModel):
    id_origin_account: int
    destination_alias: str
    destination_masked: str
    amount: float = Field(gt=0)
    currency: str = "MXN"
    concept: str = ""


class ConfirmTransferArgs(BaseModel):
    id_transfer: int
    method: Literal["app", "otp", "biometric", "app_pin"] = "app"


class GetReconciliationStatusArgs(BaseModel):
    id_user: Optional[int] = None
    id_transfer: Optional[int] = None
    id_account: Optional[int] = None
    status: Optional[Literal["pending", "matched", "mismatch"]] = None


class GetAccountSummaryArgs(BaseModel):
    id_user: int


class GetAccountDetailArgs(BaseModel):
    id_account: int


class GetAllTransactionsArgs(BaseModel):
    """Equivale a GET /me/transactions: mismos filtros que
    GetTransactionsArgs pero a través de todas las cuentas del usuario."""
    id_user: int
    id_account: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category: Optional[str] = None
    limit: int = Field(20, ge=1, le=200)


class GetTransfersArgs(BaseModel):
    id_user: int
    status: Optional[Literal["pending", "pending_confirmation", "confirmed", "failed"]] = None
    id_origin_account: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(20, ge=1, le=200)


class GetTransferDetailArgs(BaseModel):
    id_transfer: int


class GetStatementsArgs(BaseModel):
    id_account: int
    year: Optional[int] = None
    month: Optional[int] = None
    status: Optional[Literal["generated", "archived"]] = None


class GetStatementDetailArgs(BaseModel):
    id_account: int
    id_statement: int


class GetExpenseCategoriesArgs(BaseModel):
    search: Optional[str] = None


class GetBudgetsMonthlyArgs(BaseModel):
    year: int
    month: int
    category: Optional[str] = None
    status: Optional[Literal["active", "exceeded"]] = None


class GetSavingsGoalsArgs(BaseModel):
    status: Optional[Literal["active", "paused", "completed"]] = None


class GetCreditCardsArgs(BaseModel):
    status: Optional[Literal["active", "blocked", "cancelled"]] = None


class GetCreditCardStatementsArgs(BaseModel):
    id_credit_card: int
    year: Optional[int] = None
    month: Optional[int] = None


# ---------------------------------------------------------------------------
# PLAN DE ACCIÓN - VERSIÓN BANORTE ACCESSIBLE (ENRIQUECIDA)
# ---------------------------------------------------------------------------
class StepArguments(BaseModel):
    """Argumentos del paso.

    ANTES de la migración: los campos "desconocidos" se rellenaban con
    strings mágicos tipo "__PLACEHOLDER_ACCOUNT_ID__", porque el schema los
    declaraba como `str` obligatorio. Eso era un parche necesario mientras
    no había IDs reales que fueran de otro tipo.

    AHORA que la base de datos real usa IDs enteros (IdAccount, IdUser,
    IdTransfer...), el JSON Schema estricto de Groq puede declarar estos
    campos como `["integer", "null"]` / `["string", "null"]`: el modelo ya
    NO puede inventar un placeholder de texto para un campo numérico (el
    schema se lo impide), así que "no lo sé" ahora es simplemente `null`
    (-> `None` aquí). Esto vuelve obsoleto el hack de placeholders de texto
    para estos campos: no hace falta "adivinar y luego corregir", el
    schema ya fuerza la forma correcta desde el modelo.
    """
    id_user: Optional[int] = Field(default=None, description="PK de Users (IdUser)")
    id_account: Optional[int] = Field(default=None, description="PK de Accounts (IdAccount)")
    id_origin_account: Optional[int] = Field(default=None, description="Cuenta origen de una transferencia, o filtro originAccountId en get_transfers (IdOriginAccount)")
    id_session: Optional[int] = Field(default=None, description="PK de Sessions (IdSession)")
    id_transfer: Optional[int] = Field(default=None, description="PK de Transfers (IdTransfer)")
    destination_alias: Optional[str] = Field(default=None)
    destination_masked: Optional[str] = Field(default=None, description="Últimos dígitos enmascarados del destino, ej. '****5678'")
    amount: float = Field(default=0.0)
    currency: str = Field(default="MXN")
    concept: Optional[str] = Field(default=None)
    query: Optional[str] = Field(default=None)
    date_from: Optional[date] = Field(default=None)
    date_to: Optional[date] = Field(default=None)
    limit: int = Field(default=20)
    method: str = Field(default="app", description="Método de confirmación: app, otp, biometric, app_pin")
    # --- Campos agregados junto con los endpoints nuevos de Pablo (Statements,
    # Budgets, SavingsGoals, CreditCards, ExpenseCategories, /me/transactions,
    # /transfers). Igual que los de arriba: "no lo sé" es siempre null, nunca
    # un placeholder de texto inventado.
    status: Optional[str] = Field(default=None, description="Filtro de estado (varía por tool: active/blocked, pending/confirmed, generated/archived, active/exceeded, active/paused/completed...)")
    account_type: Optional[str] = Field(default=None, description="Filtro de accounts.list: 'debito' o 'credito'")
    category: Optional[str] = Field(default=None, description="Filtro de texto libre para transacciones/presupuestos (categoría)")
    expense_category: Optional[str] = Field(default=None, description="Código de app/schemas ExpenseCategory para filtrar transacciones")
    direction: Optional[str] = Field(default=None, description="Filtro de transacciones: 'credit' o 'debit'")
    search: Optional[str] = Field(default=None, description="Texto libre de búsqueda (transacciones o categorías de gasto)")
    year: Optional[int] = Field(default=None, description="Año para estados de cuenta/presupuestos")
    month: Optional[int] = Field(default=None, description="Mes (1-12) para estados de cuenta/presupuestos")
    id_statement: Optional[int] = Field(default=None, description="PK de Statements (IdStatement), para get_statement_detail")
    id_credit_card: Optional[int] = Field(default=None, description="PK de CreditCards (IdCreditCard)")


# Fuente única de verdad para los placeholders de TEXTO válidos de "steps"
# (campo -> valor canónico). Con la migración a IDs enteros, la mayoría de
# los campos ya no tiene un placeholder de texto (su "no lo sé" es `None`/
# `null`, forzado por el propio JSON Schema — ver STEP_ARGUMENTS_SCHEMA).
# Este diccionario queda casi vacío a propósito: se conserva por si algún
# campo de texto futuro sí necesita un placeholder canónico en vez de null.
STEP_ARGUMENT_PLACEHOLDER_DEFAULTS: dict[str, str] = {
    nombre: campo.default
    for nombre, campo in StepArguments.model_fields.items()
    if isinstance(campo.default, str) and "PLACEHOLDER" in campo.default
}

# Campos de StepArguments cuyo "no lo sé" real es su default declarado
# (None para IDs/fechas/texto libre, "MXN" para currency, 20 para limit,
# "app" para method). Si el modelo mete ahí un placeholder de texto
# inventado por error (ya no debería, porque el schema no lo permite, pero
# por robustez ante modelos que no respeten el schema al pie de la letra),
# el normalizador cae a este valor real en vez de dejar basura.
STEP_ARGUMENT_REAL_DEFAULTS: dict[str, object] = {
    nombre: campo.default
    for nombre, campo in StepArguments.model_fields.items()
    if nombre not in STEP_ARGUMENT_PLACEHOLDER_DEFAULTS
}

# Campos permitidos en "suggested_actions[].arguments" (schema reducido).
# Ahí lo desconocido siempre es null (nunca un placeholder de texto).
SUGGESTED_ACTION_ARGUMENT_FIELDS: list[str] = ["id_user", "id_account", "id_origin_account", "query", "limit"]

# ---------------------------------------------------------------------------
# CATÁLOGOS CANÓNICOS — alineados con los endpoints reales de
# BancaAdaptativa.Api (backend/src/BancaAdaptativa.Api/Endpoints/*.cs), para
# que "intent" y "action_id" del plan de IA siempre caigan en un valor
# consistente que el resto del equipo (Cain/Juan Pablo) pueda mapear sin
# sorpresas.
# ---------------------------------------------------------------------------
CANONICAL_INTENTS: list[str] = [
    "view_profile",            # GET /users/me
    "update_preferences",      # PUT /me/preferences
    "view_accounts",           # GET /accounts
    "view_account_summary",    # GET /me/account-summary
    "view_account_detail",     # GET /accounts/{id}
    "view_transactions",       # GET /accounts/{id}/transactions
    "view_all_transactions",   # GET /me/transactions
    "view_balance",            # GET /accounts/{id}/daily-balances
    "make_transfer",           # POST /transfers
    "confirm_transfer",        # POST /transfers/{id}/confirm
    "view_transfers",          # GET /transfers
    "view_transfer_status",    # GET /transfers/{id}
    "view_reconciliation",     # GET /reconciliation
    "view_statements",         # GET /accounts/{id}/statements
    "view_statement_detail",   # GET /accounts/{id}/statements/{id}
    "view_expense_categories", # GET /expense-categories
    "view_budgets",            # GET /me/budgets/monthly
    "view_savings_goals",      # GET /me/savings-goals
    "view_credit_cards",       # GET /me/credit-cards
    "view_credit_card_statements",  # GET /me/credit-cards/{id}/statements
    "search_memory",           # aún sin endpoint real (ver MemoryEvent)
    "provide_overview",        # sin endpoint: saludo / "qué puedes hacer"
]

# Variantes que el modelo ha devuelto y que NO son typos, sino sinónimos
# completos -> se mapean directo sin pasar por similitud de texto.
INTENT_ALIASES: dict[str, str] = {
    "general_inquiry": "provide_overview",
    "general_help": "provide_overview",
    "greeting": "provide_overview",
    "help": "provide_overview",
    "overview": "provide_overview",
    "get_overview": "provide_overview",
    "check_balance": "view_balance",
    "get_balance": "view_balance",
    "get_daily_balance": "view_balance",
    "transfer_money": "make_transfer",
    "send_money": "make_transfer",
    "get_transactions": "view_transactions",
    "get_accounts": "view_accounts",
    "get_account_detail": "view_account_detail",
    "get_user_context": "view_profile",
    "update_accessibility": "update_preferences",
    "adjust_accessibility": "update_preferences",
    "adjust_interface": "update_preferences",
    "change_theme": "update_preferences",
    "reconciliation_status": "view_reconciliation",
    "memory_search": "search_memory",
    "account_summary": "view_account_summary",
    "total_balance": "view_account_summary",
    "get_account_summary": "view_account_summary",
    "account_detail": "view_account_detail",
    "get_account_detail": "view_account_detail",
    "all_transactions": "view_all_transactions",
    "global_transactions": "view_all_transactions",
    "get_all_transactions": "view_all_transactions",
    "transfer_history": "view_transfers",
    "list_transfers": "view_transfers",
    "get_transfers": "view_transfers",
    "transfer_detail": "view_transfer_status",
    "get_transfer_detail": "view_transfer_status",
    "statements": "view_statements",
    "account_statements": "view_statements",
    "get_statements": "view_statements",
    "statement_detail": "view_statement_detail",
    "get_statement_detail": "view_statement_detail",
    "expense_categories": "view_expense_categories",
    "get_expense_categories": "view_expense_categories",
    "budgets": "view_budgets",
    "monthly_budgets": "view_budgets",
    "get_budgets_monthly": "view_budgets",
    "savings_goals": "view_savings_goals",
    "get_savings_goals": "view_savings_goals",
    "credit_cards": "view_credit_cards",
    "get_credit_cards": "view_credit_cards",
    "credit_card_statements": "view_credit_card_statements",
    "get_credit_card_statements": "view_credit_card_statements",
}

CANONICAL_ACTION_IDS: list[str] = [
    "suggest_view_balance",
    "suggest_view_transactions",
    "suggest_view_accounts",
    "suggest_make_transfer",
    "suggest_confirm_transfer",
    "suggest_add_to_contacts",
    "suggest_download_statement",
    "suggest_check_transfer",
    "suggest_view_transfer_history",
    "suggest_search_accounts",
    "suggest_update_preferences",
    "suggest_open_settings",
    "suggest_contact_support",
    "suggest_enable_high_contrast",
    "suggest_view_account_summary",
    "suggest_view_all_transactions",
    "suggest_view_statements",
    "suggest_view_budgets",
    "suggest_view_savings_goals",
    "suggest_view_credit_cards",
    "suggest_view_expense_categories",
    "suggest_view_account_detail",
    "suggest_view_transfer_detail",
    "suggest_view_statement_detail",
    "suggest_view_credit_card_statements",
    "suggest_view_reconciliation",
]

# Invenciones observadas del modelo que NO son typos sino atajos
# semánticos (ej. 'suggest_view_card_statements' cuando habla de la
# tarjeta): por similitud pura caerían en el id canónico equivocado
# ('suggest_view_statements' en vez del de tarjeta), así que se mapean
# directo sin pasar por difflib (ver plan_normalizer.py).
ACTION_ID_ALIASES: dict[str, str] = {
    "suggest_view_card_statements": "suggest_view_credit_card_statements",
    "suggest_view_card_statement": "suggest_view_credit_card_statements",
    "suggest_view_debts": "suggest_view_credit_cards",
    "suggest_view_debts_history": "suggest_view_credit_card_statements",
}

# El modelo a veces escribe el INTENT (view_balance) o un atajo en el
# campo "tool" del step/sugerencia, que solo acepta TOOL_NAMES. Por
# similitud pura algunos caerían en la tool equivocada (ej.
# 'get_card_statements' es más parecido a 'get_statements' que a
# 'get_credit_card_statements', aunque significa lo segundo), así que
# estos se mapean directo antes de usar difflib.
TOOL_ALIASES: dict[str, str] = {
    "view_profile": "get_user_context",
    "view_accounts": "get_accounts",
    "view_account_summary": "get_account_summary",
    "view_account_detail": "get_account_detail",
    "view_transactions": "get_transactions",
    "view_all_transactions": "get_all_transactions",
    "view_balance": "get_daily_balance",
    "daily_balance": "get_daily_balance",
    "make_transfer": "prepare_transfer",
    "transfer_money": "prepare_transfer",
    "send_money": "prepare_transfer",
    "view_transfers": "get_transfers",
    "transfer_history": "get_transfers",
    "list_transfers": "get_transfers",
    "view_transfer_status": "get_transfer_detail",
    "view_reconciliation": "get_reconciliation_status",
    "reconciliation_status": "get_reconciliation_status",
    "view_statements": "get_statements",
    "view_statement_detail": "get_statement_detail",
    "view_expense_categories": "get_expense_categories",
    "view_budgets": "get_budgets_monthly",
    "get_budget": "get_budgets_monthly",
    "get_budgets": "get_budgets_monthly",
    "monthly_budgets": "get_budgets_monthly",
    "view_savings_goals": "get_savings_goals",
    "savings_goals": "get_savings_goals",
    "view_credit_cards": "get_credit_cards",
    "credit_cards": "get_credit_cards",
    "view_credit_card_statements": "get_credit_card_statements",
    "get_card_statements": "get_credit_card_statements",
    "card_statements": "get_credit_card_statements",
    "search_memory": "search_memory_context",
    "memory_search": "search_memory_context",
}


class PlannedStep(BaseModel):
    step_id: str
    tool: ToolName
    ui_hint: UIHint
    arguments: StepArguments = Field(default_factory=StepArguments)
    reason: str
    visual: VisualMetadata = Field(default_factory=VisualMetadata)
    accessibility: AccessibilityMetadata
    messages: dict = Field(
        default_factory=dict,
        description="Mensajes adaptados: {default: '...', senior: '...', visual_impairment: '...'}"
    )


class ActionPlan(BaseModel):
    intent: str
    steps: list[PlannedStep] = Field(default_factory=list)
    needs_confirmation: bool = False
    response_to_user: str
    response_to_user_plain_language: Optional[str] = Field(
        default=None,
        description="Versión en lenguaje simple del mensaje"
    )
    suggested_actions: list[SuggestedAction] = Field(
        default_factory=list,
        description="Acciones relacionadas que el usuario podría querer hacer"
    )
    contextual_tips: list[str] = Field(
        default_factory=list,
        description="Consejos contextuales para el usuario"
    )
    accessibility_recommendations: list[str] = Field(
        default_factory=list,
        description="Recomendaciones de accesibilidad basadas en el perfil del usuario"
    )
    visual_theme: dict = Field(
        default_factory=dict,
        description="Tema visual sugerido: {primary_color, accent_color, icon_style}"
    )
    accessibility_template: str = Field(
        default="default",
        description=(
            "Id de la plantilla de accesibilidad a aplicar (ver "
            "app/ia/accessibility_templates.py). La IA solo elige el id; "
            "los valores reales (font_scale, color_filter, etc.) los define "
            "ese catálogo, nunca el modelo."
        ),
    )


# ---------------------------------------------------------------------------
# JSON SCHEMA para Groq (additionalProperties:false en todos los objetos,
# requerido por response_format json_schema en modo "strict")
# ---------------------------------------------------------------------------
VISUAL_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "icon": {"type": "string", "enum": [icon.value for icon in IconType]},
        "variant": {"type": "string", "enum": [v.value for v in ComponentVariant]},
        "tone": {"type": ["string", "null"], "enum": [t.value for t in BadgeTone] + [None]},
        "emphasis": {"type": "string", "enum": ["normal", "highlighted", "subtle"]},
        "animation": {"type": "string", "enum": ["none", "fade", "slide", "pulse"]}
    },
    "required": ["icon", "variant", "tone", "emphasis", "animation"],
    "additionalProperties": False
}

SENIOR_ADAPTATIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "font_scale": {"type": "number"},
        "button_size": {"type": "string", "enum": ["sm", "md", "lg"]},
        "row_height": {"type": "string"},
        "show_icons": {"type": "boolean"},
        "show_balance_prominent": {"type": "boolean"},
        "field_labels": {"type": "string"}
    },
    "required": ["font_scale", "button_size", "row_height", "show_icons", "show_balance_prominent", "field_labels"],
    "additionalProperties": False
}

VISUAL_IMPAIRMENT_ADAPTATIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "high_contrast": {"type": "boolean"},
        "audio_description": {"type": "boolean"},
        "audio_cue": {"type": "boolean"},
        "audio_confirmation": {"type": "boolean"}
    },
    "required": ["high_contrast", "audio_description", "audio_cue", "audio_confirmation"],
    "additionalProperties": False
}

ACCESSIBILITY_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "aria_label": {"type": "string"},
        "screen_reader_text": {"type": "string"},
        "focusable": {"type": "boolean"},
        "keyboard_shortcut": {"type": ["string", "null"]},
        "plain_language_text": {"type": ["string", "null"]},
        "tooltip": {"type": ["string", "null"]},
        "senior_adaptations": {
            "type": "object",
            "properties": SENIOR_ADAPTATIONS_SCHEMA["properties"],
            "required": SENIOR_ADAPTATIONS_SCHEMA["required"],
            "additionalProperties": False
        },
        "visual_impairment_adaptations": {
            "type": "object",
            "properties": VISUAL_IMPAIRMENT_ADAPTATIONS_SCHEMA["properties"],
            "required": VISUAL_IMPAIRMENT_ADAPTATIONS_SCHEMA["required"],
            "additionalProperties": False
        }
    },
    "required": [
        "aria_label", "screen_reader_text", "focusable",
        "keyboard_shortcut", "plain_language_text", "tooltip",
        "senior_adaptations", "visual_impairment_adaptations"
    ],
    "additionalProperties": False
}

MESSAGES_SCHEMA = {
    "type": "object",
    "properties": {
        "default": {"type": "string"},
        "senior": {"type": "string"},
        "visual_impairment": {"type": "string"},
        "cognitive_impairment": {"type": "string"}
    },
    "required": ["default", "senior", "visual_impairment", "cognitive_impairment"],
    "additionalProperties": False
}

# CLAVE DE LA MIGRACIÓN: los IDs ahora son ["integer", "null"] en vez de
# "string". Con response_format strict, el modelo YA NO PUEDE escribir un
# placeholder de texto en un campo numérico: solo puede dar el entero real
# o `null`. Las fechas siguen siendo string (formato ISO date), porque el
# JSON Schema no tiene un tipo "date" nativo.
STEP_ARGUMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "id_user": {"type": ["integer", "null"]},
        "id_account": {"type": ["integer", "null"]},
        "id_origin_account": {"type": ["integer", "null"]},
        "id_session": {"type": ["integer", "null"]},
        "id_transfer": {"type": ["integer", "null"]},
        "destination_alias": {"type": ["string", "null"]},
        "destination_masked": {"type": ["string", "null"]},
        "amount": {"type": "number"},
        "currency": {"type": "string"},
        "concept": {"type": ["string", "null"]},
        "query": {"type": ["string", "null"]},
        "date_from": {"type": ["string", "null"], "description": "Fecha ISO (YYYY-MM-DD) o null"},
        "date_to": {"type": ["string", "null"], "description": "Fecha ISO (YYYY-MM-DD) o null"},
        "limit": {"type": "integer"},
        "method": {"type": "string"},
        "status": {"type": ["string", "null"], "description": "Filtro de estado, depende de la tool"},
        "account_type": {"type": ["string", "null"], "description": "'debito' o 'credito'"},
        "category": {"type": ["string", "null"]},
        "expense_category": {"type": ["string", "null"]},
        "direction": {"type": ["string", "null"], "description": "'credit' o 'debit'"},
        "search": {"type": ["string", "null"]},
        "year": {"type": ["integer", "null"]},
        "month": {"type": ["integer", "null"]},
        "id_statement": {"type": ["integer", "null"]},
        "id_credit_card": {"type": ["integer", "null"]}
    },
    "required": [
        "id_user", "id_account", "id_origin_account", "id_session",
        "id_transfer", "destination_alias", "destination_masked", "amount",
        "currency", "concept", "query", "date_from", "date_to", "limit", "method",
        "status", "account_type", "category", "expense_category", "direction",
        "search", "year", "month", "id_statement", "id_credit_card"
    ],
    "additionalProperties": False
}

SUGGESTED_ACTION_ARGUMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "id_user": {"type": ["integer", "null"]},
        "id_account": {"type": ["integer", "null"]},
        "id_origin_account": {"type": ["integer", "null"]},
        "query": {"type": ["string", "null"]},
        "limit": {"type": ["integer", "null"]}
    },
    "required": ["id_user", "id_account", "id_origin_account", "query", "limit"],
    "additionalProperties": False
}

SUGGESTED_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action_id": {"type": "string"},
        "label": {"type": "string"},
        "description": {"type": "string"},
        "tool": {"type": "string", "enum": TOOL_NAMES},
        "arguments": SUGGESTED_ACTION_ARGUMENTS_SCHEMA,
        "ui_hint": {"type": "string", "enum": [hint.value for hint in UIHint]},
        "reason": {"type": "string"},
        "icon": {"type": "string", "enum": [icon.value for icon in IconType]},
        "variant": {"type": "string", "enum": [v.value for v in ComponentVariant]},
        "priority": {"type": "string", "enum": [p.value for p in Priority]}
    },
    "required": ["action_id", "label", "description", "tool", "arguments", "ui_hint", "reason", "icon", "variant", "priority"],
    "additionalProperties": False
}

VISUAL_THEME_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_color": {"type": "string"},
        "accent_color": {"type": "string"},
        "icon_style": {"type": "string"}
    },
    "required": ["primary_color", "accent_color", "icon_style"],
    "additionalProperties": False
}

ACTION_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "string"},
                    "tool": {"type": "string", "enum": TOOL_NAMES},
                    "ui_hint": {"type": "string", "enum": [hint.value for hint in UIHint]},
                    "arguments": STEP_ARGUMENTS_SCHEMA,
                    "reason": {"type": "string"},
                    "visual": VISUAL_METADATA_SCHEMA,
                    "accessibility": ACCESSIBILITY_METADATA_SCHEMA,
                    "messages": MESSAGES_SCHEMA
                },
                "required": ["step_id", "tool", "ui_hint", "arguments", "reason", "visual", "accessibility", "messages"],
                "additionalProperties": False
            }
        },
        "needs_confirmation": {"type": "boolean"},
        "response_to_user": {"type": "string"},
        "response_to_user_plain_language": {"type": ["string", "null"]},
        "suggested_actions": {"type": "array", "items": SUGGESTED_ACTION_SCHEMA},
        "contextual_tips": {"type": "array", "items": {"type": "string"}},
        "accessibility_recommendations": {"type": "array", "items": {"type": "string"}},
        "visual_theme": VISUAL_THEME_SCHEMA,
        "accessibility_template": {"type": "string", "enum": ACCESSIBILITY_TEMPLATE_IDS}
    },
    "required": [
        "intent", "steps", "needs_confirmation", "response_to_user",
        "response_to_user_plain_language", "suggested_actions",
        "contextual_tips", "accessibility_recommendations", "visual_theme",
        "accessibility_template"
    ],
    "additionalProperties": False
}

DEFAULT_UI_HINT_BY_TOOL: dict[str, str] = {
    "get_user_context": UIHint.NONE.value,
    "get_accounts": UIHint.SUMMARY.value,
    "get_account_summary": UIHint.SUMMARY.value,
    "get_account_detail": UIHint.SUMMARY.value,
    "get_transactions": UIHint.TABLE.value,
    "get_all_transactions": UIHint.TABLE.value,
    "get_daily_balance": UIHint.SUMMARY.value,
    "search_memory_context": UIHint.NONE.value,
    "prepare_transfer": UIHint.FORM.value,
    "confirm_transfer": UIHint.CONFIRMATION.value,
    "get_transfers": UIHint.TABLE.value,
    "get_transfer_detail": UIHint.SUMMARY.value,
    "get_reconciliation_status": UIHint.TABLE.value,
    "get_statements": UIHint.TABLE.value,
    "get_statement_detail": UIHint.SUMMARY.value,
    "get_expense_categories": UIHint.TABLE.value,
    "get_budgets_monthly": UIHint.SUMMARY.value,
    "get_savings_goals": UIHint.TABLE.value,
    "get_credit_cards": UIHint.TABLE.value,
    "get_credit_card_statements": UIHint.TABLE.value,
}
