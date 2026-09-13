"use client";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { EmptyState } from "@/components/states/EmptyState";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { fecha, lista, mxn } from "@/lib/plan-result";

interface Meta {
    id_goal: number;
    name: string;
    target_amount: number;
    current_amount: number;
    progress_percent: number;
    target_date: string;
    status: string;
}

// get_savings_goals (table) — tarjetas con avance.
export function SavingsGoalsList({ step }: { step: ExecutedStep }) {
    const rows = lista<Meta>(step.result);
    if (rows.length === 0)
        return <EmptyState title="Sin metas de ahorro" description="Aún no tienes metas. Crea una desde la app para empezar a ahorrar." />;
    return (
        <div className="flex flex-col gap-3">
            {rows.map((g) => (
                <Card key={g.id_goal}>
                    <div className="mb-1 flex items-center justify-between gap-2">
                        <p className="font-medium text-[var(--color-text)]">{g.name}</p>
                        <Badge tone={tonoEstado(g.status)}>{etiquetaEstado(g.status)}</Badge>
                    </div>
                    <ProgressBar
                        value={g.current_amount}
                        max={g.target_amount || 1}
                        label={`${mxn(g.current_amount)} de ${mxn(g.target_amount)} · meta ${fecha(g.target_date)}`}
                    />
                </Card>
            ))}
        </div>
    );
}
