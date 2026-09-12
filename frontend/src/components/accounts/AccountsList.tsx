"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency } from "@/components/balance/types";
import {
    getAccountsWithMeta,
    ACCOUNT_TYPE_LABELS,
    ACCOUNT_STATUS_LABELS,
} from "./types";

export function AccountsList() {
    const accounts = getAccountsWithMeta();

    return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {accounts.map((account) => (
                <Link
                    key={account.id}
                    href={`/accounts/${account.id}`}
                    className="block rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:bg-[var(--color-surface-2)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
                >
                    <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-[var(--color-text)]">
                            {account.label}
                        </span>
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

                    <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                        {ACCOUNT_TYPE_LABELS[account.accountType]} · {account.accountNumber}
                    </p>
                    <p className="mt-2 text-xl font-semibold text-[var(--color-text)]">
                        {formatCurrency(account.currentBalance, account.currency)}
                    </p>
                </Link>
            ))}
        </div>
    );
}