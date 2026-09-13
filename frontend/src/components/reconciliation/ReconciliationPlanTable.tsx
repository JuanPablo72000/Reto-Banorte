"use client";

import { Badge } from "@/components/ui/Badge";
import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { lista } from "@/lib/plan-result";

interface Match {
    id_match: number;
    id_transfer: number;
    id_transaction: number;
    status: string;
    match_score: number;
}

// get_reconciliation_status (table).
export function ReconciliationPlanTable({ step }: { step: ExecutedStep }) {
    const rows = lista<Match>(step.result);
    return (
        <Table
            caption="Conciliación transferencias-movimientos"
            columns={[
                { key: "tr", header: "Transferencia", align: "right", render: (m) => `#${m.id_transfer}` },
                { key: "tx", header: "Movimiento", align: "right", render: (m) => `#${m.id_transaction}` },
                { key: "score", header: "Score", align: "right", render: (m) => `${Math.round(m.match_score * 100)}%` },
                { key: "status", header: "Estado", render: (m) => <Badge tone={tonoEstado(m.status)}>{etiquetaEstado(m.status)}</Badge> },
            ]}
            data={rows}
            getRowId={(m) => m.id_match}
        />
    );
}
