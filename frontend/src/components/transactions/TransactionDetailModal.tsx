"use client";

import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
    Transaction,
    CATEGORY_LABELS,
    STATUS_LABELS,
    TRANSACTION_ACCOUNTS,
    formatCurrency,
} from "./types";

export interface TransactionDetailModalProps {
    transaction: Transaction | null;
    onClose: () => void;
}

export function TransactionDetailModal({
                                           transaction,
                                           onClose,
                                       }: TransactionDetailModalProps) {
    const account = TRANSACTION_ACCOUNTS.find(
        (acc) => acc.id === transaction?.accountId
    );

    return (
        <Modal
            isOpen={transaction !== null}
            onClose={onClose}
            title="Detalle de la transacción"
            footer={<Button onClick={onClose}>Cerrar</Button>}
        >
            {transaction && (
                <dl className="grid grid-cols-2 gap-y-3 gap-x-4">
                    <dt className="font-medium">Descripción</dt>
                    <dd>{transaction.description}</dd>

                    <dt className="font-medium">Cuenta</dt>
                    <dd>{account?.alias ?? transaction.accountId}</dd>

                    <dt className="font-medium">Fecha</dt>
                    <dd>{new Date(transaction.date).toLocaleDateString("es-MX")}</dd>

                    <dt className="font-medium">Categoría</dt>
                    <dd>{CATEGORY_LABELS[transaction.category]}</dd>

                    <dt className="font-medium">Estado</dt>
                    <dd>
                        <Badge
                            tone={
                                transaction.status === "completed"
                                    ? "success"
                                    : transaction.status === "pending"
                                        ? "warning"
                                        : "danger"
                            }
                        >
                            {STATUS_LABELS[transaction.status]}
                        </Badge>
                    </dd>

                    <dt className="font-medium">Referencia</dt>
                    <dd>{transaction.reference}</dd>

                    <dt className="font-medium">Monto</dt>
                    <dd
                        className={
                            transaction.direction === "in"
                                ? "text-[var(--color-success)]"
                                : "text-[var(--color-text)]"
                        }
                    >
                        {transaction.direction === "in" ? "+" : "-"}
                        {formatCurrency(transaction.amount)}
                    </dd>
                </dl>
            )}
        </Modal>
    );
}