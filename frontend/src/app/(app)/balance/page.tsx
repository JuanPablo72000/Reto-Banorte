"use client";

// Saldos: REST /me/account-summary (total + desglose) con count-up,
// fallback a mocks y bloque IA (get_daily_balance).

import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { MOCK_BALANCES, formatCurrency } from "@/components/balance/types";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { DemoBadge } from "@/components/ui/DemoBadge";
import { Icon } from "@/components/ui/Icon";
import { LineChart } from "@/components/ui/Chart";
import { LoadingState } from "@/components/states/LoadingState";
import { apiGet, type AccountSummaryResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";
import { useCountUp } from "@/lib/hooks/useCountUp";

export default function BalancePage() {
    const { session } = useAuth();
    const { data, cargando, noDisponible } = useBackendData(
        () => apiGet<AccountSummaryResponse>("/me/account-summary", session?.token),
        [session],
    );

    const total = data ? data.totalBalance : MOCK_BALANCES.reduce((s, m) => s + m.currentBalance, 0);
    const currency = data?.currency ?? "MXN";
    const animado = useCountUp(total);

    const desglose = data
        ? data.accounts.map((a) => ({ id: String(a.idAccount), label: a.alias, balance: a.balance, currency: a.currency, status: a.status }))
        : MOCK_BALANCES.map((m) => ({ id: m.id, label: m.label, balance: m.currentBalance, currency: m.currency, status: "active" }));

    const trend = (noDisponible || !data ? MOCK_BALANCES[0]?.trend : []).map((p) => ({ day: p.day, balance: p.balance }));

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl font-semibold text-[var(--color-text)]">Saldos</h2>
                    <p className="text-sm text-[var(--color-text-muted)]">Tu dinero de un vistazo.</p>
                </div>
                <DemoBadge activo={noDisponible || !data} />
            </header>

            {cargando && !data ? (
                <LoadingState message="Cargando saldos…" variant="skeleton" />
            ) : (
                <>
                    <Card className="ui-rise relative overflow-hidden bg-[var(--color-accent-dark)]! border-0!" style={{ "--orden": 1 } as React.CSSProperties}>
                        <span className="login-blob" aria-hidden="true" style={{ width: 220, height: 220, top: -80, right: -60, background: "var(--color-accent)", opacity: 0.35 }} />
                        <p className="relative text-sm text-white/80">Saldo total</p>
                        <p className="relative mt-1 text-4xl font-semibold tabular-nums text-white">
                            {formatCurrency(animado, currency)}
                        </p>
                    </Card>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {desglose.map((c, i) => (
                            <Card key={c.id} className="ui-rise card-hover flex flex-col gap-2" style={{ "--orden": i + 2 } as React.CSSProperties}>
                                <div className="flex items-center justify-between gap-2">
                                    <span className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)]">
                                        <Icon name="wallet" size={18} className="text-[var(--color-accent)]" />
                                        {c.label}
                                    </span>
                                    {c.status !== "active" && <Badge>{c.status}</Badge>}
                                </div>
                                <p className="text-xl font-semibold tabular-nums text-[var(--color-text)]">
                                    {formatCurrency(c.balance, c.currency)}
                                </p>
                            </Card>
                        ))}
                    </div>

                    {trend.length > 0 && (
                        <Card className="ui-rise" style={{ "--orden": 6 } as React.CSSProperties}>
                            <p className="mb-3 text-sm font-semibold text-[var(--color-text)]">Últimos 7 días (cuenta principal)</p>
                            <LineChart data={trend} xKey="day" yKey="balance" height={220} />
                        </Card>
                    )}
                </>
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 7 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery label="¿Cómo va mi saldo hoy?" tool="get_daily_balance" icon="chart" titulo="Saldo diario con IA" />
            </Card>
        </div>
    );
}
