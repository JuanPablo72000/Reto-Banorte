// Tipos del ActionPlan ejecutado — espejo 1:1 de mcp/app/schemas/schemas.py.
// El puente /api/chat devuelve este JSON (bloque [4] de tests/test_repl_e2e.py).

export type UIHint =
    | "form"
    | "confirmation"
    | "table"
    | "summary"
    | "none"
    | "alert"
    | "tutorial"
    | "suggestion";

export type IconType =
    | "account"
    | "transaction"
    | "transfer"
    | "balance"
    | "search"
    | "help"
    | "warning"
    | "success"
    | "info"
    | "settings"
    | "statement"
    | "budget"
    | "goal"
    | "card"
    | "category";

// Mismo vocabulario que components/ui (Button variant, Badge/Tag tone).
export type Variant = "primary" | "secondary" | "ghost" | "danger";
export type Tone = "success" | "warning" | "danger" | "info" | "neutral";
export type Priority = "high" | "medium" | "low" | "critical";

export type AnimationKind = "none" | "fade" | "slide" | "pulse";

export type AccessibilityTemplate =
    | "default"
    | "senior"
    | "low_vision"
    | "blind_screen_reader"
    | "color_blind_protanopia"
    | "color_blind_deuteranopia"
    | "color_blind_tritanopia"
    | "motor_impairment"
    | "cognitive_impairment"
    | "low_literacy";

export type ToolName =
    | "get_user_context"
    | "get_accounts"
    | "get_account_summary"
    | "get_account_detail"
    | "get_transactions"
    | "get_all_transactions"
    | "get_daily_balance"
    | "search_memory_context"
    | "prepare_transfer"
    | "confirm_transfer"
    | "get_transfers"
    | "get_transfer_detail"
    | "get_reconciliation_status"
    | "get_statements"
    | "get_statement_detail"
    | "get_expense_categories"
    | "get_budgets_monthly"
    | "get_savings_goals"
    | "get_credit_cards"
    | "get_credit_card_statements";

export type ProfileMessages = "default" | "senior" | "visual_impairment" | "cognitive_impairment";

export interface StepVisual {
    icon: IconType;
    variant: Variant;
    tone: Tone | null;
    emphasis: string;
    animation: string;
}

export interface StepResult {
    ejecutado: boolean;
    pendiente_confirmacion?: boolean;
    error?: string;
    // Lecturas: { total, muestra: [...] }; objeto único: el modelo directo.
    result?: { total: number; muestra: Record<string, unknown>[] } | Record<string, unknown>;
}

export interface ExecutedStep extends StepResult {
    step_id: string;
    tool: ToolName;
    ui_hint: UIHint;
    visual: StepVisual;
    messages: Record<ProfileMessages, string>;
}

export interface SuggestedAction {
    action_id: string;
    label: string;
    description: string;
    tool: ToolName;
    arguments: Record<string, unknown>;
    ui_hint: UIHint;
    reason: string;
    icon: IconType;
    variant: Variant;
    priority: Priority;
}

export interface VisualTheme {
    primary_color: string;
    accent_color: string;
    icon_style: string;
}

export interface ActionPlanUI {
    intent: string;
    response_to_user: string;
    response_to_user_plain_language: string;
    needs_confirmation: boolean;
    accessibility_template: AccessibilityTemplate;
    executed_steps: ExecutedStep[];
    suggested_actions: SuggestedAction[];
    contextual_tips: string[];
    accessibility_recommendations: string[];
    visual_theme: VisualTheme;
    depuracion?: { modelo: string | null; correcciones: string[] };
    error?: string;
}

export interface ChatContext {
    id_user?: number;
    id_account?: number;
    confirmado?: boolean;
    token?: string;
    // Botón de SuggestionBar clickeado: tool/arguments ya calculados por
    // el backend, para que el paso se ejecute garantizado (ver
    // orquestador.ejecutar_turno) y no dependa de que la IA reinterprete
    // el texto del botón.
    accion_directa?: {
        tool: ToolName;
        arguments: Record<string, unknown>;
        label?: string;
    };
}
