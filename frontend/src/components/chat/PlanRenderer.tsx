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
import { useVista } from "@/components/providers/VistaProvider";
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
import { attrsAnimacion } from "@/lib/atributos";
import { agruparPorSeccion, tamanoEfectivo } from "@/lib/layout";
import { aplicarPlantilla } from "@/lib/plantillas";
import type {
    AccessibilityTemplate,
    ActionPlanUI,
    ExecutedStep,
    SuggestedAction,
    ToolName,
    Visualization,
} from "@/lib/types/action-plan";
import { BarChart, LineChart, DonutChart } from "@/components/ui/Chart";
import { Card } from "@/components/ui/Card";
import BankCard from "../BankCard";

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

    // Ajuste en vivo: estado compartido con el panel de accesibilidad
    // (VistaProvider); el override local gana a la plantilla de la IA.
    const { vista } = useVista();
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

    function renderVisualization(viz: Visualization, idx: number) {
        // Si la visualización es una tarjeta bancaria
        if (viz.type === "bank_card") {
            const cardData: Record<string, unknown> = viz.data[0] ?? {};
            const texto = (k: string, defecto = ""): string => {
                const v = cardData[k];
                return typeof v === "string" ? v : typeof v === "number" ? String(v) : defecto;
            };
            const info = Array.isArray(cardData.additionalInfo)
                ? (cardData.additionalInfo as unknown[]).flatMap((r) =>
                      r && typeof r === "object" &&
                      typeof (r as Record<string, unknown>).label === "string" &&
                      typeof (r as Record<string, unknown>).value === "string"
                          ? [{ label: (r as Record<string, string>).label, value: (r as Record<string, string>).value }]
                          : [],
                  )
                : [];
            return (
                <div key={`viz-${idx}`} role="figure" aria-label={viz.accessibility_label} className="mb-4">
                    <h3 className="sr-only">{viz.title}</h3>
                    <p className="sr-only">{viz.description}</p>
                    <BankCard
                        cardNumber={texto("cardNumber")}
                        holderName={texto("holderName")}
                        expiryDate={texto("expiryDate")}
                        bankName={texto("bankName", "Banorte")}
                        balance={texto("balance")}
                        currency={texto("currency", "MXN")}
                        cardType={texto("cardType") === "credit" ? "credit" : "debit"}
                        additionalInfo={info}
                        accessibilityLabel={viz.accessibility_label}
                    />
                </div>
            );
        }

        // Gráficos tradicionales (normaliza filas a string|number)
        const filas = viz.data.map((r) => {
            const fila: Record<string, string | number> = {};
            for (const [k, v] of Object.entries(r)) {
                if (typeof v === "string" || typeof v === "number") fila[k] = v;
            }
            return fila;
        });
        const claves = Object.keys(filas[0] ?? {});
        const dataKey = claves.find((k) => k !== "name" && k !== "label" && k !== "fecha") ?? "value";
        const nameKey =
            claves.find((k) => k === "name" || k === "label" || k === "categoria") ?? claves[0] ?? "name";
        const esDona = viz.type === "pie" || viz.type === "donut";
        const ChartComponent = viz.type === "line" ? LineChart : BarChart;

        return (
            <Card key={`viz-${idx}`} className="mb-4 p-4" role="figure" aria-label={viz.accessibility_label}>
                <h3 className="mb-2 text-lg font-semibold text-[var(--color-text)]">{viz.title}</h3>
                <p className="mb-4 text-sm text-[var(--color-text-muted)]">{viz.description}</p>
                {esDona ? (
                    <DonutChart data={filas} nameKey={nameKey} valueKey={dataKey} height={280} />
                ) : (
                    <ChartComponent data={filas} xKey={nameKey} yKey={dataKey} height={280} />
                )}
                <span className="sr-only">{viz.accessibility_label}</span>
            </Card>
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
            <p
                className="ui-rise text-lg text-[var(--color-text)]"
                aria-live="polite"
                style={{ "--orden": 0 } as React.CSSProperties}
            >
                {texto}
            </p>

            <PlanLayout grupos={grupos} renderStep={renderStep} vista={vista} />

            {plan.visualizations && plan.visualizations.length > 0 && (
                <section aria-label="Visualizaciones" className="mt-4">
                    {plan.visualizations.map((viz, idx) => renderVisualization(viz, idx))}
                </section>
            )}

            {plan.suggested_actions.length > 0 && (
                <SuggestionBar sugerencias={plan.suggested_actions} onActivar={onSugerencia} />
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
