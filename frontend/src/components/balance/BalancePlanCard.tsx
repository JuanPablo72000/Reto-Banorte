"use client";

import { Card } from "@/components/ui/Card";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { fecha, lista, mxn } from "@/lib/plan-result";

interface Balance {
    date: string;
    opening_balance: number;
    income: number;
    expenses: number;
    closing_balance: number;
}

// get_daily_balance (summary) — último cierre + historial corto.
export function BalancePlanCard({ step }: { step: ExecutedStep }) {
    const rows = lista<Balance>(step.result);
    const actual = rows[rows.length - 1];
    if (!actual) return <p className="text-sm">Sin datos de balance.</p>;
    const base = actual.opening_balance + actual.income;
    const pctGastado = base > 0 ? Math.round((actual.expenses / base) * 100) : 0;
    return (
        <Card>
            <p className="text-sm text-[var(--color-text-muted)]">Saldo al {fecha(actual.date)}</p>
            <p className="text-3xl font-semibold text-[var(--color-text)]" aria-live="polite">
                {mxn(actual.closing_balance)}
            </p>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                Te gastaste {mxn(actual.expenses)} ({pctGastado}% de lo disponible)
            </p>
            <dl className="mt-3 grid grid-cols-3 gap-2 text-center text-sm">
                <div>
                    <dt className="text-[var(--color-text-muted)]">Apertura</dt>
                    <dd className="font-medium">{mxn(actual.opening_balance)}</dd>
                </div>
                <div>
                    <dt className="text-[var(--color-text-muted)]">Ingresos</dt>
                    <dd className="font-medium">+{mxn(actual.income)}</dd>
                </div>
                <div>
                    <dt className="text-[var(--color-text-muted)]">Gastos</dt>
                    <dd className="font-medium">−{mxn(actual.expenses)}</dd>
                </div>
            </dl>
        </Card>
    );
}
