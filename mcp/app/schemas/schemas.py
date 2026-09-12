"""
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
# ---------------------------------------------------------------------------
TOOL_NAMES = [
    "get_user_context",
    "get_accounts",
    "get_transactions",
    "get_daily_balance",
    "search_memory_context",
    "prepare_transfer",
    "confirm_transfer",
    "get_reconciliation_status",
]

ToolName = Literal[
    "get_user_context",
    "get_accounts",
    "get_transactions",
    "get_daily_balance",
    "search_memory_context",
    "prepare_transfer",
    "confirm_transfer",
    "get_reconciliation_status",
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
    id_origin_account: Optional[int] = Field(default=None, description="Cuenta origen de una transferencia (IdOriginAccount)")
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
    "view_account_detail",     # GET /accounts/{id}
    "view_transactions",       # GET /accounts/{id}/transactions
    "view_balance",            # GET /accounts/{id}/daily-balances
    "make_transfer",           # POST /transfers
    "confirm_transfer",        # POST /transfers/{id}/confirm
    "view_transfer_status",    # GET /transfers/{id}
    "view_reconciliation",     # GET /reconciliation
    "search_memory",           # aún sin endpoint real (ver MemoryEvent)
    "provide_overview",        # sin endpoint: saludo / "qué puedes hacer"
]

# Variantes que el modelo ha devuelto y que NO son typos, sino sinónimos
# completos -> se mapean directo sin pasar por similitud de texto.
INTENT_ALIASES: dict[str, str] = {
    "general_inquiry": "provide_overview",
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
]


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
        "method": {"type": "string"}
    },
    "required": [
        "id_user", "id_account", "id_origin_account", "id_session",
        "id_transfer", "destination_alias", "destination_masked", "amount",
        "currency", "concept", "query", "date_from", "date_to", "limit", "method"
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
    "get_transactions": UIHint.TABLE.value,
    "get_daily_balance": UIHint.SUMMARY.value,
    "search_memory_context": UIHint.NONE.value,
    "prepare_transfer": UIHint.FORM.value,
    "confirm_transfer": UIHint.CONFIRMATION.value,
    "get_reconciliation_status": UIHint.TABLE.value,
}