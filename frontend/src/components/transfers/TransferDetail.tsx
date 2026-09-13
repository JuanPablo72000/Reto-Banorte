"use client";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { campo, fecha, mxn, objeto } from "@/lib/plan-result";

// get_transfer_detail (summary) — detalle de una transferencia.
export function TransferDetail({ step }: { step: ExecutedStep }) {
    const t = objeto<Record<string, unknown>>(step.result);
    if (!t) return <p className="text-sm">Sin datos de la transferencia.</p>;
    const estado = campo<string>(t, "status", "pending");

    return (
        <Card>
            <div className="flex items-center justify-between gap-2">
                <p className="text-lg font-semibold text-[var(--color-text)]">
                    {mxn(campo<number>(t, "amount", 0), campo<string>(t, "currency", "MXN"))}
                </p>
                <Badge tone={tonoEstado(estado)}>{etiquetaEstado(estado)}</Badge>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <dt className="text-[var(--color-text-muted)]">Destino</dt>
                <dd className="text-right text-[var(--color-text)]">
                    {campo<string>(t, "destination_alias", "—")} {campo<string>(t, "destination_masked", "")}
                </dd>
                <dt className="text-[var(--color-text-muted)]">Concepto</dt>
                <dd className="text-right text-[var(--color-text)]">{campo<string>(t, "concept", "—") || "—"}</dd>
                <dt className="text-[var(--color-text-muted)]">Confirmada</dt>
                <dd className="text-right text-[var(--color-text)]">{fecha(t.confirmed_at)}</dd>
            </dl>
        </Card>
    );
}
