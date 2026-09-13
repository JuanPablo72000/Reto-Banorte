"use client";

// Cuentas: REST /accounts con fallback a mocks; balance con count-up y
// bloque IA (accion_directa get_accounts).

import Link from "next/link";
import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { MOCK_BALANCES } from "@/components/balance/types";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { DemoBadge } from "@/components/ui/DemoBadge";
import { Icon } from "@/components/ui/Icon";
import { LoadingState } from "@/components/states/LoadingState";
import { formatCurrency } from "@/components/balance/types";
import { apiGet, type AccountResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";
import { useCountUp } from "@/lib/hooks/useCountUp";

const TIPO_ETIQUETA: Record<string, string> = {
    debito: "Cuenta de débito",
    credito: "Cuenta de crédito",
    chequeo: "Cuenta corriente",
    ahorro: "Cuenta de ahorro",
};

const ESTADO_TONO: Record<string, "success" | "danger" | "neutral"> = {
    active: "success",
    blocked: "danger",
    closed: "neutral",
};

const ESTADO_TEXTO: Record<string, string> = {
    active: "Activa",
    blocked: "Bloqueada",
    closed: "Cerrada",
};

function SaldoAnimado({ monto, currency }: { monto: number; currency: string }) {
    const v = useCountUp(monto);
    return <span className="tabular-nums">{formatCurrency(v, currency)}</span>;
}

interface CuentaNormalizada {
    id: string;
    alias: string;
    numero: string;
    tipo: string;
    currency: string;
    balance: number;
    status: string;
}

function CuentaCard({ c, orden }: { c: CuentaNormalizada; orden: number }) {
    return (
        <Link
            href={`/accounts/${c.id}`}
            className="block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
        >
            <Card
                className="ui-rise card-hover flex h-full flex-col gap-4"
                style={{ "--orden": orden } as React.CSSProperties}
            >
                <div className="flex items-start justify-between gap-2">
                    <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-surface-2)] text-[var(--color-accent)]">
                        <Icon name={c.tipo === "credito" ? "card" : "wallet"} size={22} />
                    </span>
                    <Badge tone={ESTADO_TONO[c.status] ?? "neutral"}>
                        {ESTADO_TEXTO[c.status] ?? c.status}
                    </Badge>
                </div>
                <div className="flex flex-col gap-1">
                    <p className="text-base font-semibold text-[var(--color-text)]">{c.alias}</p>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        {TIPO_ETIQUETA[c.tipo] ?? c.tipo} · {c.numero}
                    </p>
                </div>
                <p className="mt-auto text-2xl font-semibold text-[var(--color-text)]">
                    <SaldoAnimado monto={c.balance} currency={c.currency} />
                </p>
                <span className="flex items-center gap-1 text-sm font-medium text-[var(--color-accent)]">
                    Ver detalle <Icon name="chevron-right" size={16} />
                </span>
            </Card>
        </Link>
    );
}

export default function AccountsPage() {
    const { session } = useAuth();
    const { data, cargando, noDisponible, error, reload } = useBackendData(
        () => apiGet<AccountResponse[]>("/accounts", session?.token),
        [session],
    );

    const cuentas: CuentaNormalizada[] = data
        ? data.map((a) => ({
              id: String(a.idAccount),
              alias: a.alias,
              numero: a.maskedNumber,
              tipo: a.accountType,
              currency: a.currency,
              balance: a.balance,
              status: a.status,
          }))
        : noDisponible
          ? MOCK_BALANCES.map((m) => ({
                id: m.id,
                alias: m.label,
                numero: m.accountNumber,
                tipo: m.id === "acc-3" ? "credito" : "debito",
                currency: m.currency,
                balance: m.currentBalance,
                status: m.id === "acc-3" ? "blocked" : "active",
            }))
          : [];

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl font-semibold text-[var(--color-text)]">Mis cuentas</h2>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        Consulta saldos y el detalle de cada cuenta.
                    </p>
                </div>
                <DemoBadge activo={noDisponible} />
            </header>

            {cargando && !data ? (
                <LoadingState message="Cargando tus cuentas…" variant="skeleton" skeletonRows={3} />
            ) : error && !noDisponible ? (
                <div role="alert" className="rounded-lg border border-[var(--color-danger-bg)] p-4 text-sm text-[var(--color-text)]">
                    No se pudieron cargar las cuentas ({error}).{" "}
                    <button type="button" onClick={reload} className="font-semibold text-[var(--color-accent)] underline">
                        Reintentar
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {cuentas.map((c, i) => (
                        <CuentaCard key={c.id} c={c} orden={i + 1} />
                    ))}
                </div>
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 5 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery
                    label="Analizar mis cuentas con IA"
                    tool="get_accounts"
                    icon="sparkle"
                    titulo="Análisis de cuentas con IA"
                />
            </Card>
        </div>
    );
}
