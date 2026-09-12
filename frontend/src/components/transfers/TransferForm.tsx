"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import {
    MOCK_ACCOUNTS,
    TransferDraft,
    formatCurrency,
} from "./types";

interface TransferFormProps {
    onSubmit: (draft: TransferDraft) => void;
    initialDraft?: Partial<TransferDraft>;
}

export function TransferForm({ onSubmit, initialDraft }: TransferFormProps) {
    const [fromAccountId, setFromAccountId] = useState(
        initialDraft?.fromAccountId ?? MOCK_ACCOUNTS[0].id
    );
    const [toAccountId, setToAccountId] = useState(
        initialDraft?.toAccountId ?? ""
    );
    const [amount, setAmount] = useState<string>(
        initialDraft?.amount ? String(initialDraft.amount) : ""
    );
    const [note, setNote] = useState(initialDraft?.note ?? "");
    const [error, setError] = useState<string | null>(null);

    const fromAccount = MOCK_ACCOUNTS.find((a) => a.id === fromAccountId);

    function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError(null);

        const numericAmount = Number(amount);

        if (!toAccountId) {
            setError("Selecciona una cuenta destino.");
            return;
        }
        if (toAccountId === fromAccountId) {
            setError("La cuenta destino debe ser distinta a la de origen.");
            return;
        }
        if (!numericAmount || numericAmount <= 0) {
            setError("Ingresa un monto válido.");
            return;
        }
        if (fromAccount && numericAmount > fromAccount.balance) {
            setError("El monto excede el saldo disponible.");
            return;
        }

        onSubmit({
            fromAccountId,
            toAccountId,
            amount: numericAmount,
            note,
        });
    }

    const fromAccountOptions = MOCK_ACCOUNTS.filter(
        (a) => a.id !== "acc-3"
    ).map((acc) => ({
        value: acc.id,
        label: `${acc.label} · ${acc.accountNumber} · ${formatCurrency(
            acc.balance,
            acc.currency
        )}`,
    }));

    const toAccountOptions = [
        { value: "", label: "Selecciona una cuenta" },
        ...MOCK_ACCOUNTS.map((acc) => ({
            value: acc.id,
            label: `${acc.label} · ${acc.accountNumber}`,
        })),
    ];

    return (
        <Card>
            <CardHeader>
                <CardTitle>Nueva transferencia</CardTitle>
            </CardHeader>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-4">
                <Select
                    id="fromAccount"
                    label="Cuenta origen"
                    value={fromAccountId}
                    onChange={(e) => setFromAccountId(e.target.value)}
                    options={fromAccountOptions}
                />

                <Select
                    id="toAccount"
                    label="Cuenta destino"
                    value={toAccountId}
                    onChange={(e) => setToAccountId(e.target.value)}
                    options={toAccountOptions}
                />

                <Input
                    id="amount"
                    label="Monto"
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                />

                <Textarea
                    id="note"
                    label="Nota (opcional)"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Ej. Renta de septiembre"
                    rows={2}
                />

                {error && (
                    <p role="alert" className="text-sm" style={{ color: "var(--color-error, #d64545)" }}>
                        {error}
                    </p>
                )}

                <Button type="submit" className="mt-2 min-h-[44px]">
                    Continuar
                </Button>
            </form>
        </Card>
    );
}