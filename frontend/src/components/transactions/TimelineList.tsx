"use client";

import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/states/EmptyState";
import { Icon } from "@/components/ui/Icon";
import { Table } from "@/components/ui/Table";
import { estadoRelevante, etiquetaCategoria, etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { fecha, lista, mxn } from "@/lib/plan-result";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { attrsAnimacion } from "@/lib/atributos";

interface Movimiento {
    id_transaction: number;
    date: string;
    description: string;
    category: string;
    direction: "credit" | "debit";
    amount: number;
    status: string;
}

// get_transactions / get_all_transactions — tabla + timeline agrupado
// por día. La vista la conmuta ViewControls con .vista-tabla/.vista-cards
// (puro CSS, una sola representación visible a la vez).
export function TimelineList({ step, indice = 0 }: { step: ExecutedStep; indice?: number }) {
    const filas = lista<Movimiento>(step.result);
    if (filas.length === 0) {
        return (
            <EmptyState
                title="Sin movimientos todavía"
                description="Cuando realices operaciones aparecerán agrupadas por día."
            />
        );
    }
    const mostrarEstado = filas.some((r) => estadoRelevante(r.status));
    const grupos: { dia: string; rows: Movimiento[] }[] = [];
    for (const f of filas) {
        const dia = fecha(f.date);
        const g = grupos.find((x) => x.dia === dia);
        if (g) g.rows.push(f);
        else grupos.push({ dia, rows: [f] });
    }
    const monto = (r: Movimiento) => (r.direction === "credit" ? r.amount : -r.amount);

    return (
        <section aria-label="Movimientos agrupados por día" {...attrsAnimacion(step.visual.animation, indice)}>
            <div className="vista-tabla">
                <Table
                    caption="Movimientos de la cuenta"
                    columns={[
                        { key: "fecha", header: "Fecha", render: (r: Movimiento) => fecha(r.date) },
                        { key: "descripcion", header: "Descripción", render: (r: Movimiento) => r.description },
                        { key: "categoria", header: "Categoría", render: (r: Movimiento) => etiquetaCategoria(r.category) },
                        {
                            key: "monto",
                            header: "Monto",
                            align: "right",
                            render: (r: Movimiento) => (
                                <span className={`tabular-nums font-medium ${monto(r) > 0 ? "text-[var(--color-success-text)]" : "text-[var(--color-text)]"}`}>
                                    {monto(r) > 0 ? "+" : "−"}{mxn(r.amount)}
                                </span>
                            ),
                        },
                        ...(mostrarEstado
                            ? [{
                                  key: "estado",
                                  header: "Estado",
                                  render: (r: Movimiento) => (
                                      <Badge tone={tonoEstado(r.status)}>{etiquetaEstado(r.status)}</Badge>
                                  ),
                              }]
                            : []),
                    ]}
                    data={filas}
                    getRowId={(r: Movimiento) => r.id_transaction}
                />
            </div>
            <div className="vista-cards flex flex-col gap-[var(--gap-stack)]">
                {grupos.map((g, gi) => (
                    <section key={g.dia} aria-labelledby={`dia-${gi}`}>
                        <h4 id={`dia-${gi}`} className="mb-[var(--gap-item)] text-sm font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
                            {g.dia}
                        </h4>
                        <ul role="list" className="relative ml-3 flex flex-col gap-[var(--gap-item)] border-l-2 border-[var(--color-border-subtle)] pl-4">
                            {g.rows.map((r) => (
                                <li
                                    key={r.id_transaction}
                                    className="relative rounded-xl bg-[var(--color-surface-2)] p-[var(--pad-card)] shadow-[var(--shadow-1)]"
                                >
                                    <span aria-hidden="true" className="absolute -left-[23px] top-4 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-surface-2)] border-2 border-[var(--color-accent)]" />
                                    <div className="flex items-start gap-2">
                                        <span aria-hidden="true" className={monto(r) > 0 ? "text-[var(--color-success-text)]" : "text-[var(--color-text-muted)]"}>
                                            <Icon name={monto(r) > 0 ? "plus" : "transfer"} size={18} />
                                        </span>
                                        <div className="flex-1">
                                            <p className="text-base font-medium text-[var(--color-text)]">{r.description}</p>
                                            <p className="text-sm text-[var(--color-text-muted)]">{etiquetaCategoria(r.category)}</p>
                                        </div>
                                        <p className={`text-base font-semibold tabular-nums ${monto(r) > 0 ? "text-[var(--color-success-text)]" : "text-[var(--color-text)]"}`}>
                                            {monto(r) > 0 ? "+" : "−"}{mxn(r.amount)}
                                        </p>
                                    </div>
                                    {estadoRelevante(r.status) && (
                                        <p className="mt-1">
                                            <Badge tone={tonoEstado(r.status)}>{etiquetaEstado(r.status)}</Badge>
                                        </p>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </section>
                ))}
            </div>
        </section>
    );
}
