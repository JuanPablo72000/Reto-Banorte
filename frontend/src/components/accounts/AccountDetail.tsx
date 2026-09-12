"use client";

import Link from "next/link";
import { Table, TableColumn } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency, BalanceTrendPoint } from "@/components/balance/types";
import {
    AccountWithMeta,
    ACCOUNT_TYPE_LABELS,
    ACCOUNT_STATUS_LABELS,
} from "./types";

export interface AccountDetailProps {
    account: AccountWithMeta;
}

export function AccountDetail({ account }: AccountDetailProps) {
    const trendColumns: TableColumn<BalanceTrendPoint>[] = [
        { key: "day", header: "Día" },
        {
            key: "balance",
            header: "Saldo",
            align: "right",
            render: (row) => formatCurrency(row.balance, account.currency),
        },
    ];

    return (
        <div className="flex flex-col gap-6">
            <Link
                href="/accounts"
                className="text-sm text-[var(--color-accent)] hover:underline"
            >
                ← Volver a cuentas
            </Link>

            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-semibold text-[var(--color-text)]">
                        {account.label}
                    </h1>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        {ACCOUNT_TYPE_LABELS[account.accountType]} · {account.accountNumber}
                    </p>
                </div>
                <Badge
                    tone={
                        account.status === "active"
                            ? "success"
                            : account.status === "blocked"
                                ? "danger"
                                : "neutral"
                    }
                >
                    {ACCOUNT_STATUS_LABELS[account.status]}
                </Badge>
            </div>

            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <p className="text-sm text-[var(--color-text-muted)]">Saldo actual</p>
                <p className="text-3xl font-bold text-[var(--color-text)]">
                    {formatCurrency(account.currentBalance, account.currency)}
                </p>
                <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                    Cuenta abierta el {new Date(account.createdAt).toLocaleDateString("es-MX")}
                </p>
            </div>

            <div>
                <h2 className="mb-3 text-lg font-medium text-[var(--color-text)]">
                    Tendencia últimos 7 días
                </h2>
                <Table<BalanceTrendPoint>
                    columns={trendColumns}
                    data={account.trend}
                    getRowId={(row) => row.day}
                />
            </div>
        </div>
    );
}