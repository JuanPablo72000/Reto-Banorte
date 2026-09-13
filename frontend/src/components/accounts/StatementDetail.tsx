"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { campo, fecha, lista, mxn, objeto } from "@/lib/plan-result";

interface Gasto {
    category_name: string;
    category_code: string;
    amount: number;
    transaction_count: number;
}

// get_statement_detail (summary) — cabecera + desglose por categoría.
export function StatementDetail({ step }: { step: ExecutedStep }) {
    const det = objeto<Record<string, unknown>>(step.result);
    const st = (det?.statement ?? {}) as Record<string, unknown>;
    const gastos = lista<Gasto>(det?.expenses);
    if (!det) return <p className="text-sm">Sin datos del estado de cuenta.</p>;

    return (
        <Card>
            <CardHeader>
                <CardTitle>
                    {fecha(st.period_start)} – {fecha(st.period_end)}
                </CardTitle>
                <span className="text-lg font-semibold">{mxn(campo<number>(st, "closing_balance", 0))}</span>
            </CardHeader>
            <Table
                caption="Desglose de gastos por categoría"
                columns={[
                    { key: "cat", header: "Categoría", render: (g) => g.category_name },
                    { key: "n", header: "Movs.", align: "right", render: (g) => String(g.transaction_count) },
                    { key: "monto", header: "Monto", align: "right", render: (g) => mxn(g.amount) },
                ]}
                data={gastos}
                getRowId={(g) => g.category_code}
            />
        </Card>
    );
}
