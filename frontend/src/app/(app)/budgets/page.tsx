"use client";

// Presupuestos y metas: REST /me/budgets/monthly (mes en curso) +
// /me/savings-goals. Sin backend: EmptyState + bloques IA.

import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { formatCurrency } from "@/components/balance/types";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { EmptyState } from "@/components/states/EmptyState";
import { LoadingState } from "@/components/states/LoadingState";
import { useCountUp } from "@/lib/hooks/useCountUp";
import {
    apiGet,
    type BudgetMonthlySummaryResponse,
    type SavingsGoalResponse,
} from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

function tonoPor(pct: number): "success" | "warning" | "danger" {
    return pct > 90 ? "danger" : pct > 70 ? "warning" : "success";
}

export default function BudgetsPage() {
    const { session } = useAuth();
    const hoy = new Date();

    const presupuestos = useBackendData(
        () =>
            apiGet<BudgetMonthlySummaryResponse>(
                `/me/budgets/monthly?year=${hoy.getFullYear()}&month=${hoy.getMonth() + 1}`,
                session?.token,
            ),
        [session],
    );
    const metas = useBackendData(() => apiGet<SavingsGoalResponse[]>("/me/savings-goals", session?.token), [session]);

    const totalGastado = presupuestos.data?.totalSpent ?? 0;
    const animado = useCountUp(totalGastado);
    const sinDatos =
        !presupuestos.cargando &&
        (!presupuestos.data || presupuestos.data.budgets.length === 0) &&
        (!metas.data || metas.data.length === 0);

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise">
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Presupuestos y metas</h2>
                <p className="text-sm text-[var(--color-text-muted)]">
                    Tu gasto de {MESES[hoy.getMonth()]} y el avance de tus metas de ahorro.
                </p>
            </header>

            {presupuestos.cargando && metas.cargando ? (
                <LoadingState message="Cargando presupuestos…" variant="skeleton" skeletonRows={4} />
            ) : sinDatos ? (
                <EmptyState
                    title="Sin presupuestos ni metas"
                    description="Crea tu primer presupuesto o pregúntale al asistente cómo van tus finanzas del mes."
                    icon={<Icon name="budget" size={40} />}
                />
            ) : (
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {presupuestos.data && presupuestos.data.budgets.length > 0 && (
                        <Card className="ui-rise" style={{ "--orden": 1 } as React.CSSProperties}>
                            <CardHeader>
                                <CardTitle>Gasto del mes</CardTitle>
                            </CardHeader>
                            <p className="text-3xl font-semibold tabular-nums text-[var(--color-text)]">
                                {formatCurrency(animado)}
                                <span className="ml-2 text-sm font-normal text-[var(--color-text-muted)]">
                                    de {formatCurrency(presupuestos.data.totalLimit)}
                                </span>
                            </p>
                            <div className="mt-5 flex flex-col gap-4">
                                {presupuestos.data.budgets.map((b, i) => (
                                    <div key={b.idBudget} className="ui-rise" style={{ "--orden": i + 2 } as React.CSSProperties}>
                                        <ProgressBar
                                            value={b.usagePercent}
                                            label={`${b.categoryName} · ${formatCurrency(b.currentSpent)} / ${formatCurrency(b.amountLimit)}`}
                                            tone={tonoPor(b.usagePercent)}
                                        />
                                    </div>
                                ))}
                            </div>
                        </Card>
                    )}

                    {metas.data && metas.data.length > 0 && (
                        <Card className="ui-rise" style={{ "--orden": 2 } as React.CSSProperties}>
                            <CardHeader>
                                <CardTitle>Metas de ahorro</CardTitle>
                            </CardHeader>
                            <div className="flex flex-col gap-5">
                                {metas.data.map((g, i) => (
                                    <div key={g.idGoal} className="ui-rise flex flex-col gap-2" style={{ "--orden": i + 1 } as React.CSSProperties}>
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)]">
                                                <Icon name="piggy" size={18} className="text-[var(--color-safe)]" />
                                                {g.name}
                                            </span>
                                            <span className="text-xs text-[var(--color-text-muted)]">
                                                {new Date(g.targetDate).toLocaleDateString("es-MX")}
                                            </span>
                                        </div>
                                        <ProgressBar
                                            value={g.progressPercent}
                                            label={`${formatCurrency(g.currentAmount)} de ${formatCurrency(g.targetAmount)}`}
                                            tone={tonoPor(100 - g.progressPercent)}
                                        />
                                    </div>
                                ))}
                            </div>
                        </Card>
                    )}
                </div>
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 5 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <div className="flex flex-wrap gap-3">
                    <CainQuery label="¿Cómo van mis presupuestos?" tool="get_budgets_monthly" icon="budget" titulo="Presupuestos con IA" />
                    <CainQuery label="Ver mis metas de ahorro" tool="get_savings_goals" icon="goal" titulo="Metas con IA" />
                </div>
            </Card>
        </div>
    );
}
