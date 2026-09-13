"use client";

import { ComponentType, useEffect, useState } from "react";
import { AccountSummaryCard } from "@/components/accounts/AccountSummaryCard";
import { AccountsPlanList } from "@/components/accounts/AccountsPlanList";
import { BudgetsSummary } from "@/components/accounts/BudgetsSummary";
import { CreditCardsTable } from "@/components/accounts/CreditCardsTable";
import { SavingsGoalsList } from "@/components/accounts/SavingsGoalsList";
import { StatementDetail } from "@/components/accounts/StatementDetail";
import { StatementsTable } from "@/components/accounts/StatementsTable";
import { UserContextCard } from "@/components/accounts/UserContextCard";
import { useA11y } from "@/components/accessibility/A11yProvider";
import { BalancePlanCard } from "@/components/balance/BalancePlanCard";
import { GenericStepCard } from "@/components/chat/GenericStepCard";
import { ReconciliationPlanTable } from "@/components/reconciliation/ReconciliationPlanTable";
import { TimelineList } from "@/components/transactions/TimelineList";
import { ExpenseCategoriesList } from "@/components/transactions/ExpenseCategoriesList";
import { TransferDetail } from "@/components/transfers/TransferDetail";
import { TransfersTable } from "@/components/transfers/TransfersTable";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { BannerInfo } from "@/components/ui/BannerInfo";
import { Modal } from "@/components/ui/Modal";
import { PlanLayout } from "@/components/chat/PlanLayout";
import { SuggestionBar } from "@/components/chat/SuggestionBar";
import { ViewControls } from "@/components/chat/ViewControls";
import { attrsAnimacion } from "@/lib/atributos";
import { agruparPorSeccion, tamanoEfectivo, useVistaEnVivo } from "@/lib/layout";
import type {
    AccessibilityTemplate,
    ActionPlanUI,
    ExecutedStep,
    SuggestedAction,
    ToolName,
} from "@/lib/types/action-plan";

export type StepCardProps = { step: ExecutedStep; indice?: number };

// tool MCP -> componente con props (result + visual + messages).
// search_memory_context y lo no mapeado caen en GenericStepCard.
const REGISTRO: Record<ToolName, ComponentType<StepCardProps>> = {
    get_user_context: UserContextCard,
    get_accounts: AccountsPlanList,
    get_account_summary: AccountSummaryCard,
    get_account_detail: AccountsPlanList,
    get_transactions: TimelineList,
    get_all_transactions: TimelineList,
    get_daily_balance: BalancePlanCard,
    search_memory_context: GenericStepCard,
    prepare_transfer: GenericStepCard,
    confirm_transfer: GenericStepCard,
    get_transfers: TransfersTable,
    get_transfer_detail: TransferDetail,
    get_reconciliation_status: ReconciliationPlanTable,
    get_statements: StatementsTable,
    get_statement_detail: StatementDetail,
    get_expense_categories: ExpenseCategoriesList,
    get_budgets_monthly: BudgetsSummary,
    get_savings_goals: SavingsGoalsList,
    get_credit_cards: CreditCardsTable,
    get_credit_card_statements: StatementsTable,
};

function mensajePara(step: ExecutedStep, plantilla: AccessibilityTemplate): string {
    const clave =
        plantilla === "default"
            ? "default"
            : (plantilla as string) in step.messages
              ? (plantilla as string)
              : "default";
    return step.messages[clave as keyof typeof step.messages] ?? step.messages.default;
}

function aplicarPlantilla(
    plantilla: AccessibilityTemplate,
    usar: ReturnType<typeof useA11y>,
    tocarContraste = true,
) {
    // Solo plantillas no-default pisan preferencias (nunca se resetea
    // lo del usuario cuando el plan trae "default"). Con override manual
    // de contraste en vivo, el usuario manda y no se toca.
    if (plantilla === "low_vision") {
        usar.setFontScale(1.75);
        if (tocarContraste) usar.setContrast("high");
    } else if (plantilla === "senior") {
        usar.setFontScale(1.5);
    } else if (plantilla === "motor_impairment") {
        usar.setFontScale(1.25);
    } else if (plantilla === "cognitive_impairment" || plantilla === "low_literacy") {
        usar.setFontScale(1.15);
    } else if (plantilla.startsWith("color_blind")) {
        usar.setPalette("colorblind");
    } else if (plantilla === "blind_screen_reader") {
        usar.setFontScale(1.25);
    }
}

export interface PlanRendererProps {
    plan: ActionPlanUI;
    onSugerencia: (accion: SuggestedAction) => void;
    onConfirmar: () => void;
}

export function PlanRenderer({ plan, onSugerencia, onConfirmar }: PlanRendererProps) {
    const a11y = useA11y();
    // El modal se abre solo cuando llega un plan NUEVO con pendiente:
    // se recuerda para qué plan ya se mostró, sin effects.
    const [vistoPara, setVistoPara] = useState<ActionPlanUI | null>(null);
    const pendiente = plan.executed_steps.some((s) => s.pendiente_confirmacion);
    const modalAbierto = pendiente && vistoPara !== plan;
    const cerrarModal = () => setVistoPara(plan);

    // Ajuste en vivo (ViewControls): estado único aquí; el override
    // local gana a la plantilla de la IA.
    const [vista, setVista] = useVistaEnVivo();
    const { size: tamanoBotones } = tamanoEfectivo(plan.accessibility_template, vista);

    useEffect(() => {
        // La plantilla de la IA solo pisa preferencias cuando NO hay
        // override manual de contraste (el usuario manda en vivo).
        aplicarPlantilla(plan.accessibility_template, a11y, vista.contraste === "auto");
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [plan.accessibility_template]);

    const texto =
        plan.accessibility_template === "default"
            ? plan.response_to_user
            : (plan.response_to_user_plain_language || plan.response_to_user);

    const grupos = agruparPorSeccion(plan.executed_steps);
    const notificaciones = new Set(grupos.notification.map((s) => s.step_id));

    function renderStep(step: ExecutedStep, indice: number) {
        const Componente = REGISTRO[step.tool] ?? GenericStepCard;
        const esBanner = notificaciones.has(step.step_id);
        return (
            <section
                key={step.step_id}
                aria-label={step.tool}
                {...attrsAnimacion(step.visual.animation, indice)}
            >
                <div className="mb-2 flex items-center gap-2">
                    <Icon name={step.visual.icon} tone={step.visual.tone} />
                    <p className="text-sm text-[var(--color-text-muted)]">
                        {mensajePara(step, plan.accessibility_template)}
                    </p>
                </div>
                {!step.ejecutado && !step.pendiente_confirmacion && (
                    <p role="alert" className="mb-2 text-sm text-[var(--color-danger)]">
                        No se pudo obtener este dato: {step.error ?? "error desconocido"}
                    </p>
                )}
                {step.pendiente_confirmacion && (
                    <p className="mb-2 text-sm text-[var(--color-warning-text)]">
                        Pendiente de tu confirmación.
                    </p>
                )}
                {step.ejecutado && !esBanner && <Componente step={step} indice={indice} />}
                {step.ejecutado && esBanner && (
                    <BannerInfo
                        title={mensajePara(step, plan.accessibility_template)}
                        tone={step.visual.tone ?? "info"}
                        icon={step.visual.icon}
                        animation={step.visual.animation}
                        orden={indice}
                    />
                )}
            </section>
        );
    }

    return (
        <div
            className="flex w-full flex-col gap-4"
            style={
                {
                    "--color-accent": plan.visual_theme?.primary_color,
                } as React.CSSProperties
            }
        >
            <ViewControls vista={vista} onChange={setVista} />
            <p className="text-lg text-[var(--color-text)]" aria-live="polite">
                {texto}
            </p>

            <PlanLayout grupos={grupos} renderStep={renderStep} vista={vista} />

            {plan.suggested_actions.length > 0 && (
                <SuggestionBar
                    sugerencias={plan.suggested_actions}
                    onActivar={onSugerencia}
                    animacion="fade"
                    orden={plan.executed_steps.length}
                />
            )}

            <Modal
                isOpen={modalAbierto}
                onClose={cerrarModal}
                title="Confirmar operación"
                footer={
                    <>
                        <Button variant="ghost" size={tamanoBotones} onClick={cerrarModal}>
                            Revisar
                        </Button>
                        <Button
                            variant="primary"
                            size={tamanoBotones}
                            onClick={() => {
                                cerrarModal();
                                onConfirmar();
                            }}
                        >
                            Confirmar
                        </Button>
                    </>
                }
            >
                <p>Hay una operación sensible pendiente. Revísala arriba y confirma para ejecutarla.</p>
            </Modal>
        </div>
    );
}
