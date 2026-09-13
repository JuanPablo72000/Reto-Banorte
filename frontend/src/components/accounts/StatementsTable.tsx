"use client";

import { Badge } from "@/components/ui/Badge";
import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { estadoRelevante, etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { fecha, lista, mxn } from "@/lib/plan-result";

interface Estado {
    id_statement?: number;
    id_credit_card_statement?: number;
    period_start: string;
    period_end: string;
    opening_balance?: number;
    closing_balance?: number;
    previous_balance?: number;
    minimum_payment?: number;
    payment_due_date?: string;
    transaction_count?: number;
    status: string;
}

// get_statements / get_credit_card_statements (table). Detecta la forma
// por presencia de closing_balance (cuenta) o previous_balance (tarjeta).
export function StatementsTable({ step }: { step: ExecutedStep }) {
    const rows = lista<Estado>(step.result);
    const mostrarEstado = rows.some((r) => estadoRelevante(r.status));
    const columnaEstado = (r: Estado) => (
        <Badge tone={tonoEstado(r.status)}>{etiquetaEstado(r.status)}</Badge>
    );
    const esTarjeta = rows.length > 0 && rows[0].closing_balance === undefined;
    if (esTarjeta) {
        return (
            <Table
                caption="Estados de cuenta de la tarjeta"
                columns={[
                    { key: "periodo", header: "Periodo", render: (r) => `${fecha(r.period_start)} – ${fecha(r.period_end)}` },
                    { key: "prev", header: "Saldo anterior", align: "right", render: (r) => mxn(r.previous_balance ?? 0) },
                    { key: "min", header: "Pago mínimo", align: "right", render: (r) => mxn(r.minimum_payment ?? 0) },
                    { key: "venc", header: "Vence", render: (r) => fecha(r.payment_due_date) },
                    ...(mostrarEstado
                        ? [{ key: "status", header: "Estado", render: columnaEstado }]
                        : []),
                ]}
                data={rows}
                getRowId={(r) => r.id_credit_card_statement ?? 0}
            />
        );
    }
    return (
        <Table
            caption="Estados de cuenta"
            columns={[
                { key: "periodo", header: "Periodo", render: (r) => `${fecha(r.period_start)} – ${fecha(r.period_end)}` },
                { key: "apertura", header: "Apertura", align: "right", render: (r) => mxn(r.opening_balance) },
                { key: "cierre", header: "Cierre", align: "right", render: (r) => mxn(r.closing_balance) },
                { key: "movs", header: "Movs.", align: "right", render: (r) => String(r.transaction_count ?? "—") },
                ...(mostrarEstado
                    ? [{ key: "status", header: "Estado", render: columnaEstado }]
                    : []),
            ]}
            data={rows}
            getRowId={(r) => r.id_statement ?? 0}
        />
    );
}
