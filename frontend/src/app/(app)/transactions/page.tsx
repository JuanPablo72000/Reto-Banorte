"use client";

// Movimientos: REST /me/transactions mapeados al tipo local, con filtros,
// tabla, modal de detalle y fallback a mocks. Bloque IA de análisis de
// gastos (get_expense_categories).

import { useMemo, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { TransactionFilters } from "@/components/transactions/TransactionFilters";
import { TransactionsTable } from "@/components/transactions/TransactionsTable";
import { TransactionDetailModal } from "@/components/transactions/TransactionDetailModal";
import {
    DEFAULT_FILTERS,
    MOCK_TRANSACTIONS,
    type Transaction,
    type TransactionFiltersState,
} from "@/components/transactions/types";
import { Card } from "@/components/ui/Card";
import { DemoBadge } from "@/components/ui/DemoBadge";
import { Icon } from "@/components/ui/Icon";
import { LoadingState } from "@/components/states/LoadingState";
import { apiGet, type TransactionResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";

const CATEGORIAS: Record<string, Transaction["category"]> = {
    nomina: "income",
    super: "other",
    transporte: "other",
    transferencia: "transfer",
};

function mapearTx(t: TransactionResponse): Transaction {
    return {
        id: `tx-${t.idTransaction}`,
        accountId: String(t.idAccount),
        date: t.date,
        amount: t.amount,
        direction: t.direction === "credit" ? "in" : "out",
        category: CATEGORIAS[t.category] ?? "other",
        description: t.description,
        status: t.status === "posted" ? "completed" : t.status === "pending" ? "pending" : "failed",
        reference: t.reference,
    };
}

export default function TransactionsPage() {
    const { session } = useAuth();
    const { data, cargando, noDisponible } = useBackendData(
        () => apiGet<TransactionResponse[]>("/me/transactions?limit=100", session?.token),
        [session],
    );
    const [filters, setFilters] = useState<TransactionFiltersState>(DEFAULT_FILTERS);
    const [seleccionada, setSeleccionada] = useState<Transaction | null>(null);

    const todas = useMemo<Transaction[]>(
        () => (noDisponible || !data ? MOCK_TRANSACTIONS : data.map(mapearTx)),
        [data, noDisponible],
    );

    const filtradas = useMemo(() => {
        return todas.filter((tx) => {
            if (filters.accountId !== "all" && tx.accountId !== filters.accountId) return false;
            if (filters.direction !== "all" && tx.direction !== filters.direction) return false;
            if (filters.category !== "all" && tx.category !== filters.category) return false;
            if (filters.dateFrom && tx.date < filters.dateFrom) return false;
            if (filters.dateTo && tx.date > filters.dateTo) return false;
            return true;
        });
    }, [todas, filters]);

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl font-semibold text-[var(--color-text)]">Movimientos</h2>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        Filtra y consulta el detalle de cada movimiento.
                    </p>
                </div>
                <DemoBadge activo={noDisponible || !data} />
            </header>

            {cargando && !data ? (
                <LoadingState message="Cargando movimientos…" variant="skeleton" skeletonRows={6} />
            ) : (
                <section className="flex flex-col gap-6">
                    <div className="ui-rise" style={{ "--orden": 1 } as React.CSSProperties}>
                        <TransactionFilters value={filters} onChange={setFilters} />
                    </div>
                    <Card className="ui-rise p-0" style={{ "--orden": 2 } as React.CSSProperties}>
                        <div data-anim-rows>
                            <TransactionsTable transactions={filtradas} onSelect={setSeleccionada} />
                        </div>
                    </Card>
                    <TransactionDetailModal transaction={seleccionada} onClose={() => setSeleccionada(null)} />
                </section>
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 3 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery
                    label="Analizar mis gastos por categoría"
                    tool="get_expense_categories"
                    icon="category"
                    titulo="Análisis de gastos con IA"
                />
            </Card>
        </div>
    );
}
