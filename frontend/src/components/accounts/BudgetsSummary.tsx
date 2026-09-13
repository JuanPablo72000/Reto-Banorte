"use client";

import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { etiquetaCategoria, etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { campo, lista, mxn, objeto } from "@/lib/plan-result";

interface Presupuesto {
    category_name?: string | null;
    category_code?: string | null;
    amount_limit: number;
    current_spent: number;
    usage_percent: number;
    status: string;
}

// get_budgets_monthly (summary) — totales + barra por categoría.
export function BudgetsSummary({ step }: { step: ExecutedStep }) {
    const data = objeto<Record<string, unknown>>(step.result);
    const items = lista<Presupuesto>(
        data && Array.isArray(data.budgets) ? data.budgets : undefined,
    );
    if (!data) return <p className="text-sm">Sin datos de presupuestos.</p>;
    const restante = campo<number>(data, "total_limit", 0) - campo<number>(data, "total_spent", 0);

    return (
        <Card>
            <CardHeader>
                <CardTitle>
                    Presupuestos {campo<number>(data, "month", 0)}/{campo<number>(data, "year", 0)}
                </CardTitle>
                <span className="text-sm text-[var(--color-text-muted)]">
                    Te quedan {mxn(restante)} de {mxn(campo<number>(data, "total_limit", 0))}
                </span>
            </CardHeader>
            <div className="flex flex-col gap-4">
                {items.map((b) => (
                    <div key={b.category_code ?? b.category_name ?? "na"}>
                        <div className="mb-1 flex items-center justify-between text-sm">
                            <span>{etiquetaCategoria(b.category_name ?? b.category_code)}</span>
                            <Badge tone={tonoEstado(b.status)}>{etiquetaEstado(b.status)}</Badge>
                        </div>
                        <ProgressBar
                            value={b.current_spent}
                            max={b.amount_limit || 1}
                            label={`${mxn(b.current_spent)} de ${mxn(b.amount_limit)}`}
                            tone={b.status === "exceeded" ? "danger" : "neutral"}
                        />
                    </div>
                ))}
            </div>
        </Card>
    );
}
