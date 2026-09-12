"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Divider } from "@/components/ui/Divider";
import {
    MOCK_ACCOUNTS,
    TransferDraft,
    formatCurrency,
} from "./types";

interface TransferConfirmationProps {
    draft: TransferDraft;
    onConfirm: () => void;
    onCancel: () => void;
    isSubmitting?: boolean;
}

export function TransferConfirmation({
                                         draft,
                                         onConfirm,
                                         onCancel,
                                         isSubmitting = false,
                                     }: TransferConfirmationProps) {
    const fromAccount = MOCK_ACCOUNTS.find((a) => a.id === draft.fromAccountId);
    const toAccount = MOCK_ACCOUNTS.find((a) => a.id === draft.toAccountId);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Confirma tu transferencia</CardTitle>
            </CardHeader>

            <div className="flex flex-col gap-4 p-4">
                <div className="flex items-center justify-between">
          <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            Estado
          </span>
                    <Badge>Pendiente de confirmación</Badge>
                </div>

                <Divider />

                <dl className="flex flex-col gap-3 text-sm">
                    <div className="flex justify-between">
                        <dt style={{ color: "var(--color-text-muted)" }}>Desde</dt>
                        <dd className="text-right">
                            {fromAccount?.label}
                            <br />
                            <span style={{ color: "var(--color-text-muted)" }}>
                {fromAccount?.accountNumber}
              </span>
                        </dd>
                    </div>

                    <div className="flex justify-between">
                        <dt style={{ color: "var(--color-text-muted)" }}>Hacia</dt>
                        <dd className="text-right">
                            {toAccount?.label}
                            <br />
                            <span style={{ color: "var(--color-text-muted)" }}>
                {toAccount?.accountNumber}
              </span>
                        </dd>
                    </div>

                    {draft.note && (
                        <div className="flex justify-between">
                            <dt style={{ color: "var(--color-text-muted)" }}>Nota</dt>
                            <dd className="text-right">{draft.note}</dd>
                        </div>
                    )}
                </dl>

                <Divider />

                <div className="flex items-center justify-between">
                    <span className="text-base font-medium">Monto a transferir</span>
                    <span className="text-xl font-semibold">
            {formatCurrency(draft.amount, fromAccount?.currency)}
          </span>
                </div>

                <div className="flex gap-3 mt-2">
                    <Button
                        type="button"
                        variant="secondary"
                        onClick={onCancel}
                        disabled={isSubmitting}
                        className="flex-1 min-h-[44px]"
                    >
                        Volver
                    </Button>
                    <Button
                        type="button"
                        onClick={onConfirm}
                        disabled={isSubmitting}
                        className="flex-1 min-h-[44px]"
                    >
                        {isSubmitting ? "Confirmando…" : "Confirmar transferencia"}
                    </Button>
                </div>
            </div>
        </Card>
    );
}