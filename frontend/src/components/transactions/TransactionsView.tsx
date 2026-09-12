"use client";

import { useMemo, useState } from "react";
import { TransactionFilters } from "./TransactionFilters";
import { TransactionsTable } from "./TransactionsTable";
import { TransactionDetailModal } from "./TransactionDetailModal";
import {
    Transaction,
    TransactionFiltersState,
    DEFAULT_FILTERS,
    MOCK_TRANSACTIONS,
} from "./types";

export function TransactionsView() {
    const [filters, setFilters] = useState<TransactionFiltersState>(DEFAULT_FILTERS);
    const [selected, setSelected] = useState<Transaction | null>(null);

    const filtered = useMemo(() => {
        return MOCK_TRANSACTIONS.filter((tx) => {
            if (filters.accountId !== "all" && tx.accountId !== filters.accountId) {
                return false;
            }
            if (filters.direction !== "all" && tx.direction !== filters.direction) {
                return false;
            }
            if (filters.category !== "all" && tx.category !== filters.category) {
                return false;
            }
            if (filters.dateFrom && tx.date < filters.dateFrom) {
                return false;
            }
            if (filters.dateTo && tx.date > filters.dateTo) {
                return false;
            }
            return true;
        });
    }, [filters]);

    return (
        <section className="flex flex-col gap-6">
            <TransactionFilters value={filters} onChange={setFilters} />
            <TransactionsTable transactions={filtered} onSelect={setSelected} />
            <TransactionDetailModal
                transaction={selected}
                onClose={() => setSelected(null)}
            />
        </section>
    );
}