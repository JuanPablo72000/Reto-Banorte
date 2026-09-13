"use client";

// Estados de cuenta: REST /accounts + /accounts/{id}/statements por cuenta.
// Sin backend: bloque IA (get_statements) como alternativa.

import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { formatCurrency } from "@/components/balance/types";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { Table, type TableColumn } from "@/components/ui/Table";
import { EmptyState } from "@/components/states/EmptyState";
import { LoadingState } from "@/components/states/LoadingState";
import { apiGet, type AccountResponse, type StatementResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";

interface Fila {
    statement: StatementResponse;
    alias: string;
}

const PERIODO = (s: StatementResponse) =>
    `${new Date(`${s.periodStart}T00:00:00`).toLocaleDateString("es-MX")} — ${new Date(
        `${s.periodEnd}T00:00:00`,
    ).toLocaleDateString("es-MX")}`;

export default function StatementsPage() {
    const { session } = useAuth();
    const [expandido, setExpandido] = useState<number | null>(null);

    const { data, cargando, noDisponible } = useBackendData(async () => {
        const cuentas = await apiGet<AccountResponse[]>("/accounts", session?.token);
        const listas = await Promise.all(
            cuentas.map(async (c) => {
                try {
                    const s = await apiGet<StatementResponse[]>(
                        `/accounts/${c.idAccount}/statements`,
                        session?.token,
                    );
                    return s.map((statement) => ({ statement, alias: c.alias }));
                } catch {
                    return [] as Fila[];
                }
            }),
        );
        return listas.flat();
    }, [session]);

    const columnas: TableColumn<Fila>[] = [
        { key: "cuenta", header: "Cuenta", render: (f) => f.alias },
        { key: "periodo", header: "Periodo", render: (f) => PERIODO(f.statement) },
        {
            key: "saldo",
            header: "Saldo final",
            align: "right",
            render: (f) => formatCurrency(f.statement.closingBalance),
        },
        { key: "movs", header: "Movimientos", align: "right", render: (f) => f.statement.transactionCount },
        {
            key: "status",
            header: "Estado",
            render: (f) => (
                <Badge tone={f.statement.status === "generated" ? "success" : "neutral"}>
                    {f.statement.status === "generated" ? "Generado" : f.statement.status}
                </Badge>
            ),
        },
    ];

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise">
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Estados de cuenta</h2>
                <p className="text-sm text-[var(--color-text-muted)]">
                    Historial mensual por cuenta con saldos y desglose.
                </p>
            </header>

            {cargando ? (
                <LoadingState message="Cargando estados de cuenta…" variant="skeleton" skeletonRows={4} />
            ) : data && data.length > 0 ? (
                <Card className="ui-rise p-0" style={{ "--orden": 1 } as React.CSSProperties}>
                    <div data-anim-rows>
                        <Table
                            columns={columnas}
                            data={data}
                            getRowId={(f) => f.statement.idStatement}
                            caption="Estados de cuenta generados"
                        />
                    </div>
                    <div className="flex flex-col gap-2 p-4">
                        {data.map((f) => (
                            <button
                                key={f.statement.idStatement}
                                type="button"
                                onClick={() =>
                                    setExpandido((v) => (v === f.statement.idStatement ? null : f.statement.idStatement))
                                }
                                aria-expanded={expandido === f.statement.idStatement}
                                className="flex min-h-[44px] items-center justify-between gap-2 rounded-lg border border-[var(--color-border)] px-4 text-sm font-medium text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-2)] motion-reduce:transition-none"
                            >
                                <span className="flex items-center gap-2">
                                    <Icon name="statement" size={18} className="text-[var(--color-accent)]" />
                                    {f.alias} · {PERIODO(f.statement)}
                                </span>
                                <Icon
                                    name={expandido === f.statement.idStatement ? "chevron-up" : "chevron-down"}
                                    size={16}
                                />
                            </button>
                        ))}
                        {expandido !== null &&
                            (() => {
                                const f = data.find((x) => x.statement.idStatement === expandido);
                                if (!f) return null;
                                const s = f.statement;
                                return (
                                    <div className="ui-pop grid grid-cols-2 gap-3 rounded-lg bg-[var(--color-surface-2)] p-4 text-sm sm:grid-cols-4">
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Saldo inicial</p>
                                            <p className="font-semibold tabular-nums text-[var(--color-text)]">{formatCurrency(s.openingBalance)}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Créditos</p>
                                            <p className="font-semibold tabular-nums text-[var(--color-text)]">{formatCurrency(s.totalCredits)}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Cargos</p>
                                            <p className="font-semibold tabular-nums text-[var(--color-text)]">{formatCurrency(s.totalDebits)}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Día de corte</p>
                                            <p className="font-semibold text-[var(--color-text)]">Día {s.cutOffDay}</p>
                                        </div>
                                    </div>
                                );
                            })()}
                    </div>
                </Card>
            ) : (
                <EmptyState
                    title="Sin estados de cuenta"
                    description={
                        noDisponible
                            ? "El servidor de datos no está disponible. Pídeselos al asistente."
                            : "Aún no hay estados generados. Puedes pedir un resumen al asistente."
                    }
                    icon={<Icon name="statement" size={40} />}
                />
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 2 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery
                    label="Consultar mis estados de cuenta"
                    tool="get_statements"
                    icon="statement"
                    titulo="Estados de cuenta con IA"
                />
            </Card>
        </div>
    );
}
