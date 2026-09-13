"use client";

// Conciliación: REST /reconciliation (transferencias vs movimientos) con
// tabla; sin backend, el bloque IA (get_reconciliation_status).

import { useAuth } from "@/components/auth/AuthProvider";
import { CainQuery } from "@/components/chat/CainQuery";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { Table, type TableColumn } from "@/components/ui/Table";
import { EmptyState } from "@/components/states/EmptyState";
import { LoadingState } from "@/components/states/LoadingState";
import { apiGet, type ReconciliationResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";

const ESTADO_TONO: Record<string, "success" | "warning" | "danger" | "neutral"> = {
    matched: "success",
    pending: "warning",
    unmatched: "danger",
};

const ESTADO_TEXTO: Record<string, string> = {
    matched: "Conciliado",
    pending: "Pendiente",
    unmatched: "Sin coincidencia",
};

export default function ReconciliationPage() {
    const { session } = useAuth();
    const { data, cargando, noDisponible } = useBackendData(
        () => apiGet<ReconciliationResponse[]>("/reconciliation", session?.token),
        [session],
    );

    const columnas: TableColumn<ReconciliationResponse>[] = [
        { key: "idMatch", header: "Folio", render: (r) => `#${r.idMatch}` },
        { key: "idTransfer", header: "Transferencia", render: (r) => `T-${r.idTransfer}` },
        { key: "idTransaction", header: "Movimiento", render: (r) => `M-${r.idTransaction}` },
        {
            key: "matchScore",
            header: "Confianza",
            align: "right",
            render: (r) => `${Math.round(r.matchScore * 100)}%`,
        },
        {
            key: "status",
            header: "Estado",
            render: (r) => (
                <Badge tone={ESTADO_TONO[r.status] ?? "neutral"}>
                    {ESTADO_TEXTO[r.status] ?? r.status}
                </Badge>
            ),
        },
        {
            key: "matchedAt",
            header: "Fecha",
            render: (r) => (r.matchedAt ? new Date(r.matchedAt).toLocaleDateString("es-MX") : "—"),
        },
    ];

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise">
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Conciliación</h2>
                <p className="text-sm text-[var(--color-text-muted)]">
                    Verifica que tus transferencias coincidan con los movimientos registrados.
                </p>
            </header>

            {cargando ? (
                <LoadingState message="Conciliando…" variant="skeleton" skeletonRows={4} />
            ) : data && data.length > 0 ? (
                <Card className="ui-rise p-0" style={{ "--orden": 1 } as React.CSSProperties}>
                    <div data-anim-rows>
                        <Table columns={columnas} data={data} getRowId={(r) => r.idMatch} caption="Conciliaciones" />
                    </div>
                </Card>
            ) : (
                <EmptyState
                    title={noDisponible ? "Servidor no disponible" : "Todo en orden"}
                    description={
                        noDisponible
                            ? "No hay datos de conciliación locales. Pídele el estado al asistente."
                            : "No hay conciliaciones pendientes por ahora."
                    }
                    icon={<Icon name="shield" size={40} />}
                />
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 2 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery
                    label="Estado de conciliación"
                    tool="get_reconciliation_status"
                    icon="shield"
                    titulo="Conciliación con IA"
                />
            </Card>
        </div>
    );
}
