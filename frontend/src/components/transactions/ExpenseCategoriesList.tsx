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

// get_expense_categories (donut + desglose) — gasto REAL por categoría
// (total_amount/transaction_count vienen ya agregados desde el backend),
// no solo el catálogo de nombres.
//
// Vista por defecto: lista espaciosa con barra de participación (ya no se
// "aplasta" la tabla de 4 columnas en el panel del plan). Con
// data-vista="tabla" (panel de accesibilidad) se muestra la tabla clásica.
export function ExpenseCategoriesList({ step }: { step: ExecutedStep }) {
    const rows = lista<Categoria>(step.result);
    const conGasto = rows.filter((c) => (c.total_amount ?? 0) > 0);
    const total = conGasto.reduce((acc, c) => acc + c.total_amount, 0);

    if (rows.length === 0) {
        return <p className="text-sm text-[var(--color-text-muted)]">Sin categorías de gasto disponibles.</p>;
    }

    const ordenadas = [...rows].sort((a, b) => (b.total_amount ?? 0) - (a.total_amount ?? 0));

    return (
        <div className="flex flex-col gap-4">
            {conGasto.length > 0 && (
                <DonutChart
                    data={conGasto.map((c) => ({ name: c.name, monto: c.total_amount }))}
                    nameKey="name"
                    valueKey="monto"
                    height={240}
                />
            )}

            {/* Vista tarjetas (default): filas amplias con barra de participación */}
            <div className="vista-cards flex-col gap-3" role="list" aria-label="Gastos por categoría">
                {ordenadas.map((c, i) => {
                    const pct = total > 0 && c.total_amount > 0 ? (c.total_amount / total) * 100 : 0;
                    return (
                        <div
                            key={c.id_category}
                            role="listitem"
                            className="ui-rise flex flex-col gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-1)] transition-shadow hover:shadow-[var(--shadow-2)] motion-reduce:transition-none"
                            style={{ "--orden": Math.min(i, 8) } as React.CSSProperties}
                        >
                            <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                                <span className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text)]">
                                    <span
                                        aria-hidden="true"
                                        className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-2)] text-xs font-bold uppercase text-[var(--color-accent)]"
                                    >
                                        {c.name.slice(0, 2)}
                                    </span>
                                    {c.name}
                                    <span className="font-normal text-[var(--color-text-muted)]">
                                        · {c.transaction_count ?? 0} movs.
                                    </span>
                                </span>
                                <span className="text-sm font-semibold tabular-nums text-[var(--color-text)]">
                                    {mxn(c.total_amount ?? 0)}
                                </span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div
                                    role="progressbar"
                                    aria-valuenow={Math.round(pct)}
                                    aria-valuemin={0}
                                    aria-valuemax={100}
                                    aria-label={`Participación de ${c.name} en el gasto total`}
                                    className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--color-surface-2)]"
                                >
                                    <div
                                        className="h-full rounded-full bg-[var(--color-accent)] transition-[width] duration-500 motion-reduce:transition-none"
                                        style={{ width: `${Math.max(pct, 1)}%` }}
                                    />
                                </div>
                                <span className="w-12 text-right text-xs font-medium tabular-nums text-[var(--color-text-muted)]">
                                    {pct > 0 ? `${Math.round(pct)}%` : "—"}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Vista tabla (data-vista="tabla" desde el panel de accesibilidad) */}
            <div className="vista-tabla" data-anim-rows>
                <Table
                    caption="Gastos por categoría"
                    columns={[
                        { key: "name", header: "Categoría", render: (c) => <span className="whitespace-nowrap font-medium">{c.name}</span> },
                        { key: "n", header: "Movs.", align: "right", render: (c) => String(c.transaction_count ?? 0) },
                        { key: "monto", header: "Gastado", align: "right", render: (c) => <span className="whitespace-nowrap tabular-nums">{mxn(c.total_amount ?? 0)}</span> },
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
                    data={ordenadas}
                    getRowId={(c) => c.id_category}
                />
            </div>
        </div>
    );
}
