"use client";

import { Badge } from "@/components/ui/Badge";
import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { lista, mxn } from "@/lib/plan-result";

interface Traspaso {
    id_transfer: number;
    destination_alias: string;
    amount: number;
    currency: string;
    status: string;
}

// get_transfers (table).
export function TransfersTable({ step }: { step: ExecutedStep }) {
    const rows = lista<Traspaso>(step.result);
    return (
        <Table
            caption="Historial de transferencias"
            columns={[
                { key: "dest", header: "Destino", render: (t) => t.destination_alias },
                { key: "monto", header: "Monto", align: "right", render: (t) => mxn(t.amount, t.currency) },
                { key: "status", header: "Estado", render: (t) => <Badge tone={tonoEstado(t.status)}>{etiquetaEstado(t.status)}</Badge> },
            ]}
            data={rows}
            getRowId={(t) => t.id_transfer}
        />
    );
}
