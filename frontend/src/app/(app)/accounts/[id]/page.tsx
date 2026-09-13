"use client";

// Detalle de cuenta: REST /accounts/{id} + movimientos + balances diarios
// (gráfica). Si el id es de los mocks (acc-*) o el backend no está, usa los
// datos demo locales.

import { use } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { MOCK_BALANCES, formatCurrency } from "@/components/balance/types";
import { MOCK_TRANSACTIONS, type Transaction } from "@/components/transactions/types";
import { TransactionsTable } from "@/components/transactions/TransactionsTable";
import { TransactionDetailModal } from "@/components/transactions/TransactionDetailModal";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { DemoBadge } from "@/components/ui/DemoBadge";
import { Icon } from "@/components/ui/Icon";
import { LineChart } from "@/components/ui/Chart";
import { LoadingState } from "@/components/states/LoadingState";
import { EmptyState } from "@/components/states/EmptyState";
import {
    apiGet,
    type AccountResponse,
    type DailyBalanceResponse,
    type TransactionResponse,
} from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";
import { useCountUp } from "@/lib/hooks/useCountUp";
import { useState } from "react";
import { useRouter } from "next/navigation";

function mapearTx(t: TransactionResponse, accountId: string): Transaction {
    const CATEGORIAS: Record<string, Transaction["category"]> = {
        nomina: "income",
        super: "other",
        transporte: "other",
        transferencia: "transfer",
    };
    return {
        id: `tx-${t.idTransaction}`,
        accountId,
        date: t.date,
        amount: t.amount,
        direction: t.direction === "credit" ? "in" : "out",
        category: CATEGORIAS[t.category] ?? "other",
        description: t.description,
        status: t.status === "posted" ? "completed" : t.status === "pending" ? "pending" : "failed",
        reference: t.reference,
    };
}

export default function AccountDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const { session } = useAuth();
    const router = useRouter();
    const [seleccionada, setSeleccionada] = useState<Transaction | null>(null);
    const esNumerico = /^\d+$/.test(id);

    const cuenta = useBackendData(
        () => apiGet<AccountResponse>(`/accounts/${id}`, session?.token),
        [id, session],
    );
    const movimientos = useBackendData(
        () => apiGet<TransactionResponse[]>(`/accounts/${id}/transactions?limit=50`, session?.token),
        [id, session],
    );
    const balances = useBackendData(
        () => apiGet<DailyBalanceResponse[]>(`/accounts/${id}/daily-balances`, session?.token),
        [id, session],
    );

    // Fallback demo
    const mock = MOCK_BALANCES.find((m) => m.id === id);
    const demo = !esNumerico || cuenta.noDisponible;
    const alias = demo ? mock?.label ?? "Cuenta" : (cuenta.data?.alias ?? "…");
    const balance = demo ? (mock?.currentBalance ?? 0) : (cuenta.data?.balance ?? 0);
    const currency = demo ? (mock?.currency ?? "MXN") : (cuenta.data?.currency ?? "MXN");
    const animado = useCountUp(balance);

    const txs: Transaction[] = demo
        ? MOCK_TRANSACTIONS.filter((t) => !esNumerico && t.accountId === id)
        : (movimientos.data ?? []).map((t) => mapearTx(t, id));

    const trend = demo
        ? (mock?.trend ?? []).map((p) => ({ day: p.day, balance: p.balance }))
        : (balances.data ?? []).map((b) => ({ day: b.date.slice(5), balance: b.closingBalance }));

    if (!demo && cuenta.cargando && !cuenta.data) {
        return (
            <div className="p-6">
                <LoadingState message="Cargando cuenta…" variant="skeleton" />
            </div>
        );
    }
    if (!demo && cuenta.error) {
        return (
            <div className="p-6">
                <EmptyState
                    title="Cuenta no encontrada"
                    description="El servidor no pudo darte esta cuenta."
                    actionLabel="Volver a cuentas"
                    onAction={() => router.push("/accounts")}
                />
            </div>
        );
    }

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <nav aria-label="Miga de pan" className="ui-rise text-sm">
                <Link href="/accounts" className="inline-flex items-center gap-1 font-medium text-[var(--color-accent)] hover:underline">
                    <Icon name="chevron-right" size={14} className="rotate-180" /> Cuentas
                </Link>
            </nav>

            <header className="ui-rise flex flex-wrap items-center justify-between gap-3" style={{ "--orden": 1 } as React.CSSProperties}>
                <div className="flex items-center gap-3">
                    <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-[var(--shadow-1)]">
                        <Icon name="wallet" size={24} />
                    </span>
                    <div>
                        <h2 className="text-xl font-semibold text-[var(--color-text)]">{alias}</h2>
                        <p className="text-sm text-[var(--color-text-muted)]">
                            {demo ? id : cuenta.data?.maskedNumber} · {currency}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <DemoBadge activo={demo} />
                    {!demo && cuenta.data && (
                        <Badge tone={cuenta.data.status === "active" ? "success" : "neutral"}>
                            {cuenta.data.status}
                        </Badge>
                    )}
                </div>
            </header>

            <Card className="ui-rise" style={{ "--orden": 2 } as React.CSSProperties}>
                <p className="text-sm text-[var(--color-text-muted)]">Saldo disponible</p>
                <p className="mt-1 text-3xl font-semibold tabular-nums text-[var(--color-text)]">
                    {formatCurrency(animado, currency)}
                </p>
            </Card>

            {trend.length > 0 && (
                <Card className="ui-rise" style={{ "--orden": 3 } as React.CSSProperties}>
                    <CardHeader>
                        <CardTitle>Evolución del saldo</CardTitle>
                    </CardHeader>
                    <LineChart data={trend} xKey="day" yKey="balance" height={220} />
                </Card>
            )}

            <Card className="ui-rise p-0" style={{ "--orden": 4 } as React.CSSProperties}>
                <CardHeader className="px-4 pt-4">
                    <CardTitle>Movimientos recientes</CardTitle>
                </CardHeader>
                <div data-anim-rows>
                    <TransactionsTable transactions={txs} onSelect={setSeleccionada} />
                </div>
            </Card>
            <TransactionDetailModal transaction={seleccionada} onClose={() => setSeleccionada(null)} />

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 5 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery
                    label="Resumir esta cuenta con IA"
                    tool="get_account_detail"
                    args={esNumerico ? { id_account: Number(id) } : {}}
                    icon="sparkle"
                    titulo="Resumen de cuenta con IA"
                />
            </Card>
        </div>
    );
}
