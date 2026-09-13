"use client";

// Ruta /transfers: formulario manual por pasos que compone el mensaje y
// lo manda por el flujo normal del chat (IA -> confirmación -> ejecución),
// más el historial REST de transferencias del backend.

import { ErrorState } from "@/components/states/ErrorState";
import { GenerandoPanel } from "@/components/chat/GenerandoPanel";
import { PlanRenderer } from "@/components/chat/PlanRenderer";
import { TransferManualForm } from "@/components/transfers/TransferManualForm";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { Table, type TableColumn } from "@/components/ui/Table";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiGet, type TransferResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";
import { formatCurrency } from "@/components/balance/types";
import { useChatPlan } from "@/lib/hooks/useChatPlan";

const ESTADO_TONO: Record<string, "success" | "warning" | "danger" | "neutral"> = {
    confirmed: "success",
    completed: "success",
    pending_confirmation: "warning",
    pending: "warning",
    rejected: "danger",
    failed: "danger",
};

const ESTADO_TEXTO: Record<string, string> = {
    confirmed: "Confirmada",
    pending_confirmation: "Pendiente de confirmación",
    rejected: "Rechazada",
};

export default function TransfersPage() {
    const chat = useChatPlan();
    const { session } = useAuth();

    // Historial REST; si el backend no está disponible (modo demo) se oculta.
    const { data: historial, error: historialError } = useBackendData(
        () => apiGet<TransferResponse[]>("/transfers", session?.token),
        [session],
    );

    const columnas: TableColumn<TransferResponse>[] = [
        {
            key: "createdAt",
            header: "Fecha",
            render: (t) => new Date(t.createdAt).toLocaleDateString("es-MX"),
        },
        { key: "destinationAlias", header: "Destino", render: (t) => `${t.destinationAlias} · ${t.destinationMasked}` },
        { key: "concept", header: "Concepto" },
        { key: "amount", header: "Monto", align: "right", render: (t) => formatCurrency(t.amount, t.currency) },
        {
            key: "status",
            header: "Estado",
            render: (t) => (
                <Badge tone={ESTADO_TONO[t.status] ?? "neutral"}>
                    {ESTADO_TEXTO[t.status] ?? t.status}
                </Badge>
            ),
        },
    ];

    return (
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl font-semibold text-[var(--color-text)]">Transferencias</h2>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        Captura los datos y el asistente se encarga, con tu confirmación.
                    </p>
                </div>
                {chat.plan && (
                    <Button variant="ghost" size="sm" onClick={chat.nuevaConsulta}>
                        <Icon name="plus" size={16} /> Otra transferencia
                    </Button>
                )}
            </header>

            {!chat.plan && !chat.cargando && !chat.error && (
                <div className="ui-rise" style={{ "--orden": 1 } as React.CSSProperties}>
                    <TransferManualForm onListo={(m) => void chat.enviar(m)} />
                </div>
            )}

            {chat.cargando && <GenerandoPanel etiqueta="Preparando tu transferencia" />}

            {chat.error && <ErrorState description={chat.error} onRetry={chat.ultimoMensaje ? chat.reintentar : undefined} />}

            {chat.plan && !chat.cargando && !chat.error && (
                <PlanRenderer plan={chat.plan} onSugerencia={chat.enviarSugerencia} onConfirmar={chat.confirmar} />
            )}

            {historial && historial.length > 0 && (
                <Card className="ui-rise p-0" style={{ "--orden": 2 } as React.CSSProperties}>
                    <CardHeader className="px-4 pt-4">
                        <CardTitle>Historial de transferencias</CardTitle>
                    </CardHeader>
                    <div data-anim-rows>
                        <Table columns={columnas} data={historial} getRowId={(t) => t.idTransfer} caption="Transferencias realizadas" />
                    </div>
                </Card>
            )}
            {historialError && (
                <p className="text-sm text-[var(--color-text-muted)]">
                    No se pudo cargar el historial desde el servidor.
                </p>
            )}
        </div>
    );
}
