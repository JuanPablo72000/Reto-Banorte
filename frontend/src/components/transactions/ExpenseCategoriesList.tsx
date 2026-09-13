"use client";

import { Table } from "@/components/ui/Table";
import { DonutChart } from "@/components/ui/Chart";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { lista, mxn } from "@/lib/plan-result";

interface Categoria {
    id_category: number;
    name: string;
    code: string;
    icon?: string | null;
    total_amount: number;
    transaction_count: number;
}

// get_expense_categories (donut + tabla) — gasto REAL por categoría
// (total_amount/transaction_count vienen ya agregados desde el backend),
// no solo el catálogo de nombres.
export function ExpenseCategoriesList({ step }: { step: ExecutedStep }) {
    const rows = lista<Categoria>(step.result);
    const conGasto = rows.filter((c) => (c.total_amount ?? 0) > 0);
    const total = conGasto.reduce((acc, c) => acc + c.total_amount, 0);

    if (rows.length === 0) {
        return <p className="text-sm text-[var(--color-text-muted)]">Sin categorías de gasto disponibles.</p>;
    }

    return (
        <div className="flex flex-col gap-4">
            {conGasto.length > 0 && (
                <DonutChart
                    data={conGasto.map((c) => ({ name: c.name, monto: c.total_amount }))}
                    nameKey="name"
                    valueKey="monto"
                    height={220}
                />
            )}
            <Table
                caption="Gastos por categoría"
                columns={[
                    { key: "name", header: "Categoría", render: (c) => c.name },
                    { key: "n", header: "Movs.", align: "right", render: (c) => String(c.transaction_count ?? 0) },
                    { key: "monto", header: "Gastado", align: "right", render: (c) => mxn(c.total_amount ?? 0) },
                    {
                        key: "pct",
                        header: "% del total",
                        align: "right",
                        render: (c) =>
                            total > 0 && c.total_amount > 0
                                ? `${Math.round((c.total_amount / total) * 100)}%`
                                : "—",
                    },
                ]}
                data={rows}
                getRowId={(c) => c.id_category}
            />
        </div>
    );
}
