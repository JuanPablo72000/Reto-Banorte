"use client";

import { Table, TableColumn } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import {
    ReconciliationMatch,
    RECONCILIATION_STATUS_LABELS,
} from "./types";

export interface ReconciliationTableProps {
    matches: ReconciliationMatch[];
}

export function ReconciliationTable({ matches }: ReconciliationTableProps) {
    const columns: TableColumn<ReconciliationMatch>[] = [
        {
            key: "transferId",
            header: "Transferencia",
        },
        {
            key: "transactionId",
            header: "Transacción",
            render: (row) => row.transactionId ?? "— (sin aparecer aún)",
        },
        {
            key: "status",
            header: "Estado",
            render: (row) => (
                <Badge
                    tone={
                        row.status === "matched"
                            ? "success"
                            : row.status === "pending"
                                ? "warning"
                                : "danger"
                    }
                >
                    {RECONCILIATION_STATUS_LABELS[row.status]}
                </Badge>
            ),
        },
        {
            key: "matchScore",
            header: "Score",
            align: "right",
            render: (row) =>
                row.matchScore !== null ? `${Math.round(row.matchScore * 100)}%` : "—",
        },
        {
            key: "matchedAt",
            header: "Fecha",
            render: (row) =>
                row.matchedAt
                    ? new Date(row.matchedAt).toLocaleDateString("es-MX")
                    : "—",
        },
        {
            key: "notes",
            header: "Notas",
        },
    ];

    return (
        <Table<ReconciliationMatch>
            columns={columns}
            data={matches}
            getRowId={(row) => row.id}
            caption="Estado de conciliación de transferencias"
        />
    );
}