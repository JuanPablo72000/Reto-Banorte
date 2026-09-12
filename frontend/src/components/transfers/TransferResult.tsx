"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
    MOCK_ACCOUNTS,
    TransferDraft,
    TransferStatus,
    formatCurrency,
} from "./types";

interface TransferResultProps {
    draft: TransferDraft;
    status: Exclude<TransferStatus, "draft" | "pending_confirmation">;
    onDone: () => void;
    onRetry?: () => void;
}

function getStatusCopy(status: TransferResultProps["status"]) {
    switch (status) {
        case "confirmed":
            return {
                title: "Transferencia confirmada",
                description: "El dinero fue enviado correctamente.",
            };
        case "failed":
            return {
                title: "No se pudo completar la transferencia",
                description: "Hubo un problema al procesar la operación. Intenta de nuevo.",
            };
        case "expired":
            return {
                title: "La confirmación expiró",
                description: "Pasó demasiado tiempo sin confirmar. Vuelve a iniciar la transferencia.",
            };
        case "cancelled":
            return {
                title: "Transferencia cancelada",
                description: "Cancelaste esta transferencia antes de completarse.",
            };
    }
}

export function TransferResult({
                                   draft,
                                   status,
                                   onDone,
                                   onRetry,
                               }: TransferResultProps) {
    const fromAccount = MOCK_ACCOUNTS.find((a) => a.id === draft.fromAccountId);
    const copy = getStatusCopy(status);
    const canRetry = status === "failed" || status === "expired";

    return (
        <Card>
            <CardHeader>
                <CardTitle>{copy.title}</CardTitle>
            </CardHeader>

            <div className="flex flex-col gap-4 p-4" role="status" aria-live="polite">
                <Badge>{status}</Badge>

                <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                    {copy.description}
                </p>

                {status === "confirmed" && (
                    <p className="text-xl font-semibold">
                        {formatCurrency(draft.amount, fromAccount?.currency)} enviados
                    </p>
                )}

                <div className="flex gap-3 mt-2">
                    {canRetry && onRetry && (
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={onRetry}
                            className="flex-1 min-h-[44px]"
                        >
                            Reintentar
                        </Button>
                    )}
                    <Button
                        type="button"
                        onClick={onDone}
                        className="flex-1 min-h-[44px]"
                    >
                        Volver al inicio
                    </Button>
                </div>
            </div>
        </Card>
    );
}