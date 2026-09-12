"use client";

import { Table, TableColumn } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import {
    Transaction,
    CATEGORY_LABELS,
    STATUS_LABELS,
    formatCurrency,
} from "./types";

export interface TransactionsTableProps {
    transactions: Transaction[];
    onSelect: (transaction: Transaction) => void;
}

export function TransactionsTable({ transactions, onSelect }: TransactionsTableProps) {
    const columns: TableColumn<Transaction>[] = [
        {
            key: "date",
            header: "Fecha",
            render: (row) => new Date(row.date).toLocaleDateString("es-MX"),
        },
        {
            key: "description",
            header: "Descripción",
            render: (row) => (
                <button
                    onClick={() => onSelect(row)}
                    className="text-left underline-offset-2 hover:underline focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
                >
                    {row.description}
                </button>
            ),
        },
        {
            key: "category",
            header: "Categoría",
            render: (row) => CATEGORY_LABELS[row.category],
        },
        {
            key: "status",
            header: "Estado",
            render: (row) => (
                <Badge
                    tone={
                        row.status === "completed"
                            ? "success"
                            : row.status === "pending"
                                ? "warning"
                                : "danger"
                    }
                >
                    {STATUS_LABELS[row.status]}
                </Badge>
            ),
        },
        {
            key: "amount",
            header: "Monto",
            align: "right",
            render: (row) => (
                <span
                    className={
                        row.direction === "in"
                            ? "text-[var(--color-success)]"
                            : "text-[var(--color-text)]"
                    }
                >
                    {row.direction === "in" ? "+" : "-"}
                    {formatCurrency(row.amount)}
                </span>
            ),
        },
    ];

    return (
        <Table<Transaction>
            columns={columns}
            data={transactions}
            getRowId={(row) => row.id}
            caption="Historial de movimientos"
        />
    );
}